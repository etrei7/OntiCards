# -*- coding:utf-8 -*-
"""
@File: test_libreoffice_concurrent_profile.py
@Description: 回归测试 - LibreOffice 并发转换的独立 profile 隔离
@Create: 2026-10-22

验证 _run_local_soffice 在并发调用时使用独立临时用户配置目录，
避免多个 soffice 进程共享同一 profile 导致的冲突。

运行方式：
    pytest controllers/governance/test_libreoffice_concurrent_profile.py -v

前置条件：
    pip install pytest
"""

import os
import pathlib
import sys
import tempfile
import threading
import time
from unittest import mock
from typing import List, Optional
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from controllers.governance.libreoffice_exporter import _run_local_soffice


class TestConcurrentProfileIsolation:
    """验证并发调用使用独立 profile 目录"""

    def test_missing_soffice_returns_none_without_profile(self):
        """缺少转换器时直接返回 None，不创建 profile 目录"""
        created_dirs: List[str] = []
        original_mkdtemp = tempfile.mkdtemp

        def tracking_mkdtemp(*args, **kwargs):
            d = original_mkdtemp(*args, **kwargs)
            if kwargs.get('prefix', '').startswith('onticards_lo_profile_'):
                created_dirs.append(d)
            return d

        with mock.patch('controllers.governance.libreoffice_exporter.tempfile.mkdtemp', side_effect=tracking_mkdtemp):
            with mock.patch('controllers.governance.libreoffice_exporter._get_local_soffice_path', return_value=None):
                result = _run_local_soffice('/tmp/fake.html', '/tmp/out', 'pdf')

        assert result is None
        assert len(created_dirs) == 0, "缺少 soffice 时不应创建 profile 目录"

    def test_profile_dir_created_and_cleaned(self):
        """每次调用创建并清理独立 profile 目录"""
        created_dirs: List[str] = []
        original_mkdtemp = tempfile.mkdtemp

        def tracking_mkdtemp(*args, **kwargs):
            d = original_mkdtemp(*args, **kwargs)
            if kwargs.get('prefix', '').startswith('onticards_lo_profile_'):
                created_dirs.append(d)
            return d

        class FakeResult:
            returncode = 0
            stdout = ''
            stderr = ''

        with mock.patch('controllers.governance.libreoffice_exporter.tempfile.mkdtemp', side_effect=tracking_mkdtemp):
            with mock.patch('controllers.governance.libreoffice_exporter._get_local_soffice_path', return_value='/usr/bin/soffice'):
                with mock.patch('controllers.governance.libreoffice_exporter.subprocess.run', return_value=FakeResult()):
                    with mock.patch('os.path.isfile', return_value=True):
                        with mock.patch('os.listdir', return_value=['fake.pdf']):
                            result = _run_local_soffice('/tmp/fake.html', '/tmp/out', 'pdf')

        assert result is not None
        assert len(created_dirs) == 1
        assert not os.path.exists(created_dirs[0]), "profile 目录应在 finally 中清理"

    def test_concurrent_calls_use_different_profiles(self):
        """并发调用必须使用不同的 profile 目录，且调用期间目录存在"""
        profile_dirs: List[str] = []
        dirs_during_call: List[List[str]] = []
        results: List[Optional[str]] = []
        lock = threading.Lock()
        creation_barrier = threading.Barrier(3, timeout=10)
        snapshot_barrier = threading.Barrier(3, timeout=10)
        original_mkdtemp = tempfile.mkdtemp

        def tracking_mkdtemp(*args, **kwargs):
            d = original_mkdtemp(*args, **kwargs)
            if kwargs.get('prefix', '').startswith('onticards_lo_profile_'):
                with lock:
                    profile_dirs.append(d)
            return d

        class FakeResult:
            returncode = 0
            stdout = ''
            stderr = ''

        def fake_run(cmd, *args, **kwargs):
            creation_barrier.wait()
            with lock:
                snapshot = [d for d in profile_dirs if os.path.isdir(d)]
                dirs_during_call.append(snapshot)
            snapshot_barrier.wait()
            return FakeResult()

        exceptions: List[Exception] = []

        def run_conversion():
            try:
                result = _run_local_soffice('/tmp/fake.html', '/tmp/out', 'pdf')
                with lock:
                    results.append(result)
            except Exception as e:
                with lock:
                    exceptions.append(e)

        with mock.patch('controllers.governance.libreoffice_exporter.tempfile.mkdtemp', side_effect=tracking_mkdtemp):
            with mock.patch('controllers.governance.libreoffice_exporter._get_local_soffice_path', return_value='/usr/bin/soffice'):
                with mock.patch('controllers.governance.libreoffice_exporter.subprocess.run', side_effect=fake_run):
                    with mock.patch('os.path.isfile', return_value=True):
                        with mock.patch('os.listdir', return_value=['fake.pdf']):
                            threads = [threading.Thread(target=run_conversion) for _ in range(3)]
                            for t in threads:
                                t.start()
                            for t in threads:
                                t.join(timeout=30)

        assert not exceptions, f"线程异常: {exceptions}"
        assert all(not t.is_alive() for t in threads), "所有线程应结束"
        assert len(results) == 3, "三次调用均应返回结果"
        assert all(r is not None for r in results), "三次转换均应成功返回非 None"
        assert len(profile_dirs) == 3
        assert len(set(profile_dirs)) == 3, "每个并发调用必须使用独立的 profile 目录"
        for snapshot in dirs_during_call:
            assert len(snapshot) >= 2, "并发期间至少两个 profile 目录同时存在"
        for d in profile_dirs:
            assert not os.path.exists(d), "所有 profile 目录应被清理"

    def test_profile_uri_format(self):
        """profile URI 必须是合法的 file:// 格式"""
        captured_cmd: List[List[str]] = []

        class FakeResult:
            returncode = 1
            stdout = ''
            stderr = ''

        def capturing_run(cmd, *args, **kwargs):
            captured_cmd.append(cmd)
            return FakeResult()

        with mock.patch('controllers.governance.libreoffice_exporter.subprocess.run', side_effect=capturing_run):
            with mock.patch('controllers.governance.libreoffice_exporter._get_local_soffice_path', return_value='/usr/bin/soffice'):
                _run_local_soffice('/tmp/test.html', '/tmp/out', 'pdf')

        assert len(captured_cmd) == 1
        cmd = captured_cmd[0]
        user_install_args = [a for a in cmd if a.startswith('-env:UserInstallation=')]
        assert len(user_install_args) == 1, "命令必须包含 -env:UserInstallation 参数"
        uri = user_install_args[0].split('=', 1)[1]
        assert uri.startswith('file://'), f"UserInstallation 必须是 file:// URI，实际为: {uri}"

    def test_profile_uri_decodes_chinese_and_spaces(self):
        """含空格/中文临时目录的 URI 可正确解码回原路径"""
        base_dir = tempfile.mkdtemp(prefix='onticards 测试 ')
        try:
            profile_subdir = os.path.join(base_dir, '带空格 中文 dir')
            os.makedirs(profile_subdir, exist_ok=True)
            uri = pathlib.Path(profile_subdir).as_uri()
            decoded = unquote(uri.replace('file://', '', 1))
            assert decoded == profile_subdir
        finally:
            import shutil
            shutil.rmtree(base_dir, ignore_errors=True)

    def test_cleanup_on_exception(self):
        """异常时仍清理 profile 目录"""
        created_dirs: List[str] = []
        original_mkdtemp = tempfile.mkdtemp

        def tracking_mkdtemp(*args, **kwargs):
            d = original_mkdtemp(*args, **kwargs)
            if kwargs.get('prefix', '').startswith('onticards_lo_profile_'):
                created_dirs.append(d)
            return d

        def raising_run(*args, **kwargs):
            raise RuntimeError("simulated failure")

        with mock.patch('controllers.governance.libreoffice_exporter.tempfile.mkdtemp', side_effect=tracking_mkdtemp):
            with mock.patch('controllers.governance.libreoffice_exporter._get_local_soffice_path', return_value='/usr/bin/soffice'):
                with mock.patch('controllers.governance.libreoffice_exporter.subprocess.run', side_effect=raising_run):
                    result = _run_local_soffice('/tmp/fake.html', '/tmp/out', 'pdf')

        assert result is None
        assert len(created_dirs) == 1
        assert not os.path.exists(created_dirs[0]), "异常后 profile 目录必须清理"

    def test_cleanup_on_timeout(self):
        """超时时仍清理 profile 目录"""
        import subprocess as sp
        created_dirs: List[str] = []
        original_mkdtemp = tempfile.mkdtemp

        def tracking_mkdtemp(*args, **kwargs):
            d = original_mkdtemp(*args, **kwargs)
            if kwargs.get('prefix', '').startswith('onticards_lo_profile_'):
                created_dirs.append(d)
            return d

        def timeout_run(*args, **kwargs):
            raise sp.TimeoutExpired(cmd='soffice', timeout=120)

        with mock.patch('controllers.governance.libreoffice_exporter.tempfile.mkdtemp', side_effect=tracking_mkdtemp):
            with mock.patch('controllers.governance.libreoffice_exporter._get_local_soffice_path', return_value='/usr/bin/soffice'):
                with mock.patch('controllers.governance.libreoffice_exporter.subprocess.run', side_effect=timeout_run):
                    result = _run_local_soffice('/tmp/fake.html', '/tmp/out', 'pdf')

        assert result is None
        assert len(created_dirs) == 1
        assert not os.path.exists(created_dirs[0]), "超时后 profile 目录必须清理"

    def test_original_command_params_preserved(self):
        """修复不改变原有转换参数（headless, convert-to, infilter, outdir, timeout）"""
        captured_kwargs = {}
        captured_cmd = []

        def capturing_run(cmd, *args, **kwargs):
            captured_cmd.append(cmd)
            captured_kwargs.update(kwargs)
            class FakeResult:
                returncode = 0
                stdout = ''
                stderr = ''
            return FakeResult()

        with mock.patch('controllers.governance.libreoffice_exporter.subprocess.run', side_effect=capturing_run):
            with mock.patch('controllers.governance.libreoffice_exporter._get_local_soffice_path', return_value='/usr/bin/soffice'):
                with mock.patch('os.path.isfile', return_value=True):
                    with mock.patch('os.listdir', return_value=['test.pdf']):
                        _run_local_soffice('/tmp/test.html', '/tmp/out', 'pdf')

        assert captured_kwargs.get('timeout') == 120, "必须保留 120 秒超时"
        assert captured_kwargs.get('capture_output') is True
        assert captured_kwargs.get('text') is True

        cmd = captured_cmd[0]
        assert '--headless' in cmd
        assert '--convert-to' in cmd
        idx = cmd.index('--convert-to')
        assert cmd[idx + 1] == 'pdf'
        assert '--outdir' in cmd

    def test_infilter_preserved_for_docx(self):
        """docx/xlsx 转换时保留 --infilter 参数"""
        captured_cmd = []

        class FakeResult:
            returncode = 1
            stdout = ''
            stderr = ''

        def capturing_run(cmd, *args, **kwargs):
            captured_cmd.append(cmd)
            return FakeResult()

        with mock.patch('controllers.governance.libreoffice_exporter.subprocess.run', side_effect=capturing_run):
            with mock.patch('controllers.governance.libreoffice_exporter._get_local_soffice_path', return_value='/usr/bin/soffice'):
                _run_local_soffice('/tmp/test.html', '/tmp/out', 'docx')

        cmd = captured_cmd[0]
        infilter_args = [a for a in cmd if a.startswith('--infilter=')]
        assert len(infilter_args) == 1
        assert 'HTML (StarWriter)' in infilter_args[0]


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
