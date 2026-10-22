// Operator-only setup, uses the existing native settings API, not credential forgery.
import {createRequire} from 'node:module';
const require=createRequire('/usr/src/app/package.json');
const {db}=await import(require.resolve('@propr/core'));
const config=await import('/usr/src/app/dist/packages/api/mcp/configResolver.js');
try {
  const before=await config.loadMcpAdminSettings(db);
  await config.saveMcpAdminSettingRows({enabled:'true',scope_ceiling:JSON.stringify(['read','review']),connect_enabled:'false'},db);
  config.invalidateMcpConfigCache();
  const after=await config.loadMcpAdminSettings(db);
  console.log('ONTICARDS_MCP_SETTINGS:'+JSON.stringify({before:{enabled:before.enabled,scopeCeiling:before.scopeCeiling,connectEnabled:before.connectEnabled},after:{enabled:after.enabled,scopeCeiling:after.scopeCeiling,connectEnabled:after.connectEnabled}}));
} finally {await db.destroy();}
