'use strict';

const fs = require('node:fs');
const path = require('node:path');

async function main() {
  const spec = path.resolve(process.argv[2]);
  let Parser;
  try {
    ({ Parser } = require(process.env.CT04_ASYNCAPI_PARSER || '@asyncapi/parser'));
  } catch {
    console.error('SETUP_REQUIRED: @asyncapi/parser@3.6.6; set CT04_ASYNCAPI_PARSER to an installed module path. No automatic install.');
    process.exitCode = 3;
    return;
  }
  const { document, diagnostics } = await new Parser().parse(fs.readFileSync(spec, 'utf8'), { source: spec });
  const result = {
    document_created: Boolean(document),
    errors: diagnostics.filter(item => item.severity === 0),
    warnings: diagnostics.filter(item => item.severity === 1),
    information: diagnostics.filter(item => item.severity > 1),
  };
  console.log(JSON.stringify(result));
  process.exitCode = !document || result.errors.length ? 1 : 0;
}

main().catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});
