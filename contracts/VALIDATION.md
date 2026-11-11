# CT-02 — Validation và cách chạy lại

**DRAFT 0.1.0-draft.1, 11/11/2026.** Validation chỉ kiểm specification, schema, examples và sự nhất quán của fixtures. Không chứng minh backend/OCR/auth/AWS/browser đã hoạt động. Công cụ được cài trong thư mục tạm ngoài repo, không đổi package.json, pnpm-lock.yaml hoặc pyproject.toml.

## Kết quả thực tế

| Kiểm tra | Kết quả |
| --- | --- |
| OpenAPI 3.1.0 bằng openapi-spec-validator | PASS, 50 operations/45 paths, path params/security/required/schema/examples có mặt |
| AsyncAPI 3.0.0 bằng @asyncapi/parser | PASS: tạo được document, 0 errors, 0 warnings; 1 **information** khuyên dùng AsyncAPI 3.1.0. Giữ 3.0.0 đã chọn cho draft, không giấu diagnostic hoặc tự nâng version |
| JSON Schema Draft-07 meta-validation | PASS, 5 schema files |
| Local $ref resolution | PASS, 908 reference occurrences, không tải schema bên ngoài |
| Fixtures | 128 positive hợp lệ; 11 negative schema bị từ chối; 5 negative semantic bị từ chối đúng nhóm; tổng 144 |
| Embedded HTTP examples | 21 request bodies, 59 success JSON responses và 396 error-example occurrences hợp lệ; 204 được kiểm tra không body. Đây không phải 396 tình huống backend độc lập |
| AsyncAPI examples | 18 payload examples hợp lệ |
| Semantic invariants | Public box edges, Unicode CP/coverage, source/snapshot/event identity và UTF-8 budget; schema-only không đủ chứng minh các phép toán này |
| Cross-fixture scenarios | 3 checks: cùng job/frame khi retry, late source khác current source, duplicate event cùng identity; không phải runtime dedup/idempotency tests |
| Raw compatibility | 3 dataclass field sets BoundingBox/Word/Paragraph khớp raw schema qua Python AST; không siết raw bbox numbers, không import/chạy model |
| Source/cấu hình/tài liệu cũ | PASS: 133 file có sẵn giữ nguyên byte-for-byte; file mới chỉ trong contracts/ và docs/CT-02-INTEGRATION-GUIDE.md (ngoài cache/build artifacts) |

Tool versions đã dùng: Python 3.14.7; openapi-spec-validator 0.7.2; jsonschema 4.26.0; referencing 0.36.2; PyYAML 6.0.3; @asyncapi/parser 3.6.6; Node v22.23.4. Các lệnh tạm không là runtime được chọn cho backend. Kết quả máy đọc ở [validation-report.json](validation-report.json).

Các lần kiểm đầu đã phát hiện sai vị trí schemaFormat khi chuyển AsyncAPI v2→v3; đã sửa sang payload Multi Format Schema Object và kiểm lại đạt. Validator Python dùng CLI OpenAPI với đường dẫn file để resolver xử lý đúng external refs; không bỏ qua lỗi unresolved refs.

## Tái lập trên máy hiện tại

Chạy từ root repository. Chỉ cài tools vào thư mục tạm, không cài dependencies ứng dụng. Máy khác có thể đổi prefix tạm và đường dẫn require tương ứng trong đoạn JavaScript.

```bash
python3 -m venv /private/tmp/ct02-validator-venv
/private/tmp/ct02-validator-venv/bin/pip install 'openapi-spec-validator==0.7.2' 'jsonschema==4.26.0' 'referencing==0.36.2' 'PyYAML==6.0.3'
npm install --prefix /private/tmp/ct02-asyncapi-validation --ignore-scripts --no-audit --no-fund '@asyncapi/parser@3.6.6'
```

Trích hai khối kiểm định bên dưới ra thư mục tạm rồi chạy. Không thực thi scripts ứng dụng/provider hoặc gửi request tới examples.invalid.

```bash
python3 - <<'EXTRACT'
from pathlib import Path
import re
text = Path('contracts/VALIDATION.md').read_text()
for language, filename in [('python', 'ct02-validate-contracts.py'), ('javascript', 'ct02-validate-asyncapi.cjs')]:
    code = re.search(r'^```' + language + r'\n(.*?)^```', text, re.M | re.S).group(1)
    Path('/private/tmp', filename).write_text(code)
EXTRACT
/private/tmp/ct02-validator-venv/bin/python /private/tmp/ct02-validate-contracts.py
node /private/tmp/ct02-validate-asyncapi.cjs
```

Hai khối code này là công cụ kiểm contract nằm trong tài liệu, không phải application backend/test server. JSON Schema validation không thực hiện quyền truy cập, uniqueness transactions, byte upload thật, deadline, signed URL expiry hoặc worker ack; các test đó cần implementation và CT-04 sau review.

## Python: schema/examples/fixtures/semantic checks

```python
from pathlib import Path
import ast,copy,hashlib,importlib.metadata,json,math,re,sys
from urllib.parse import urljoin,urldefrag,unquote,urlparse
import yaml
from jsonschema import Draft7Validator,FormatChecker
from referencing import Registry,Resource
from referencing.jsonschema import DRAFT7
from openapi_spec_validator import validate_spec
ROOT=Path.cwd();C=ROOT/'contracts'
def strict_json(path):return json.loads(path.read_text(),parse_constant=lambda v:(_ for _ in ()).throw(ValueError('Non-finite JSON number '+v)))
def load(path):return yaml.safe_load(path.read_text()) if path.suffix=='.yaml' else strict_json(path)
paths=list((C/'schemas').glob('*.json'))+[C/'openapi.yaml',C/'asyncapi.yaml']
docs={p.resolve().as_uri():load(p) for p in paths}
reg=Registry().with_resources((uri,Resource.from_contents(d,default_specification=DRAFT7)) for uri,d in docs.items())
for p in (C/'schemas').glob('*.json'):Draft7Validator.check_schema(load(p))
# Every reference resolves locally; never silently fetch arbitrary remote schemas.
refs=0
def walk_refs(v,base):
 global refs
 if isinstance(v,dict):
  if '$ref' in v:
   uri=urljoin(base,v['$ref']);docuri,fragment=urldefrag(uri)
   assert docuri in docs,uri
   cur=docs[docuri]
   for part in fragment.strip('/').split('/') if fragment else []:cur=cur[part.replace('~1','/').replace('~0','~')]
   refs+=1
  for x in v.values():walk_refs(x,base)
 elif isinstance(v,list):
  for x in v:walk_refs(x,base)
for uri,d in docs.items():walk_refs(d,uri)
import subprocess
subprocess.run([sys.executable,'-m','openapi_spec_validator',str(C/'openapi.yaml')],check=True,capture_output=True,text=True)
def validator(schema,base):
 if '$ref' in schema:return Draft7Validator({'$ref':urljoin(base,schema['$ref'])},registry=reg,format_checker=FormatChecker())
 return Draft7Validator(schema,registry=reg,format_checker=FormatChecker())
def resolve(v,base):
 while isinstance(v,dict) and '$ref' in v:
  uri=urljoin(base,v['$ref']);docuri,frag=urldefrag(uri);v=docs[docuri]
  for part in frag.strip('/').split('/') if frag else []:v=v[part.replace('~1','/').replace('~0','~')]
  base=docuri
 return v,base
# Semantic invariants cannot all be expressed by JSON Schema arithmetic / UTF-8 budgets.
def semantic(value,kind=None):
 issues=[]
 def visit(v):
  if isinstance(v,dict):
   if 'offset_unit' in v and 'tokens' in v:
    text=v['text'];cursor=0
    for t in v['tokens']:
     a,b=t['start'],t['end']
     if not(0<=a<b<=len(text)) or a!=cursor or text[a:b]!=t['surface']:issues.append('code-point-offset/coverage')
     cursor=b
    if cursor!=len(text):issues.append('incomplete-token-coverage')
   if 'ocr' in v and 'image' in v:
    if v['image']['width_px']*v['image']['height_px']>4000000:issues.append('pixel-budget')
    for para in v['ocr'].get('paragraphs',[]):
     for x in [para]+para.get('words',[]):
      b=x['box'];cx,cy,w,h=[b[k] for k in ['center_x','center_y','width','height']]
      if not all(math.isfinite(x) for x in [cx,cy,w,h]) or not(0<=cx-w/2<=cx+w/2<=1 and 0<=cy-h/2<=cy+h/2<=1):issues.append('public-box-crosses-edge')
   if 'schema_version' in v:
    size=len(json.dumps(v,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8'))
    if 'client_message_id' in v:
     if size>=1500:issues.append('chime-utf8-budget')
    elif size>24576:issues.append('ws-utf8-budget')
    if v.get('type')=='ocr.result_available':
     if v['seq']!=v['data']['seq'] or v['session_id']!=v['data']['session_id']:issues.append('event-manifest-identity')
    if v.get('type')=='session.source_changed' and v['session_id']!=v['data']['source']['session_id']:issues.append('source-event-scope')
    if v.get('type')=='session.subscribed':
     if v['session_id']!=v['data']['session']['session_id'] or v['data']['latest_seq']!=v['data']['session']['latest_seq']:issues.append('snapshot-watermark-scope')
   if 'capture_limits' in v and 'current_source_id' in v:
    source=v['current_source']
    if (source is None)!=(v['current_source_id'] is None) or (source is not None and (source['source_id']!=v['current_source_id'] or source['session_id']!=v['session_id'])):issues.append('snapshot-source-identity')
   for x in v.values():visit(x)
  elif isinstance(v,list):
   for x in v:visit(x)
 visit(value);return issues
manifest=load(C/'fixtures/manifest.json');counts={'positive_fixtures':0,'negative_schema_fixtures':0,'negative_semantic_fixtures':0,'http_request_examples':0,'http_response_examples':0,'http_failure_examples':0,'asyncapi_message_examples':0}
errors=[]
for row in manifest['files']:
 value=load(C/'fixtures'/row['file']);sch={'$ref':row['schema']};sv=list(validator(sch,(C/'fixtures/manifest.json').as_uri()).iter_errors(value));se=semantic(value)
 if row['expect_valid']:
  if sv or se:errors.append({'file':row['file'],'schema':[x.message for x in sv[:2]],'semantic':se})
  counts['positive_fixtures']+=1
 elif row.get('validation_scope')=='semantic':
  if sv or not se:errors.append({'file':row['file'],'expected':'schema valid and semantic rejection','schema':[x.message for x in sv[:2]],'semantic':se})
  counts['negative_semantic_fixtures']+=1
 else:
  if not sv:errors.append({'file':row['file'],'expected':'schema rejection'})
  counts['negative_schema_fixtures']+=1
# Validate every embedded HTTP example against its effective referenced schema.
oas=docs[(C/'openapi.yaml').as_uri()];ids=[]
for path,item in oas['paths'].items():
 for method,op in item.items():
  if method not in ['get','post','patch','delete','put']:continue
  ids.append(op['operationId']);assert op['security'] and op['x-contract-status']=='DRAFT'
  actual_params=[]
  for p in op.get('parameters',[]):actual_params.append(resolve(p,(C/'openapi.yaml').as_uri())[0])
  assert {p['name'] for p in actual_params if p['in']=='path'}==set(re.findall(r'\{([^}]+)\}',path))
  assert all(p['required'] for p in actual_params if p['in']=='path')
  if 'requestBody' in op:
   for media,content in op['requestBody']['content'].items():
    for ex in content['examples'].values():
     validator(content['schema'],(C/'openapi.yaml').as_uri()).validate(ex['value']);assert not semantic(ex['value'])
     counts['http_request_examples']+=1
  success=0;fail=0
  for status,response in op['responses'].items():
   response,base=resolve(response,(C/'openapi.yaml').as_uri())
   if status=='204':assert 'content' not in response;success+=1;continue
   for content in response.get('content',{}).values():
    for ex in content.get('examples',{}).values():
     validator(content['schema'],base).validate(ex['value']);assert not semantic(ex['value'])
     if status.startswith('2'):success+=1;counts['http_response_examples']+=1
     else:fail+=1;counts['http_failure_examples']+=1
  assert success and fail,op['operationId']
assert len(ids)==len(set(ids))==50
asy=docs[(C/'asyncapi.yaml').as_uri()]
for message in asy['components']['messages'].values():
 schema=message['payload']['schema']
 for ex in message['examples']:
  validator(schema,(C/'asyncapi.yaml').as_uri()).validate(ex['payload']);assert not semantic(ex['payload']);counts['asyncapi_message_examples']+=1
# Check cross-fixture equality and stale-source branch; these are consistency checks, not runtime UI tests.
def f(name):return load(C/'fixtures'/name)
a=f('http/duplicate-job-new.json')['data'];b=f('http/duplicate-job-retry.json')['data'];done=f('http/job-succeeded.json')['data']
assert a['job_id']==b['job_id']==done['job_id'] and a['frame_id']==b['frame_id']==done['frame_id']
assert done['result_id']==f('http/getOcrResult-200.json')['data']['result_id']
assert f('http/current-source-after-switch.json')['data']['current_source_id']!=f('http/late-result-old-source.json')['data']['source_id']
assert f('ws/duplicate-result-event.json')==f('ws/ocr-result_available.json')
lex=f('lexicon/unicode-code-points.json');assert len(lex['text'])==6 and len(lex['text'].encode('utf-16-le'))//2==7
# Raw contract field compatibility via Python AST, without importing or changing provider/model code.
tree=ast.parse((ROOT/'meikipop-ocr-server/src/meikipop_ocr_server/ocr/interface.py').read_text());raw=load(C/'schemas/ocr-provider.schema.json')
for cls in ['BoundingBox','Word','Paragraph']:
 node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
 assert {n.target.id for n in node.body if isinstance(n,ast.AnnAssign)}==set(raw['definitions'][cls]['properties'])
assert all('minimum' not in x and 'maximum' not in x for x in raw['definitions']['BoundingBox']['properties'].values())
counts.update(http_operations=len(ids),local_refs_resolved=refs,json_schemas=5,cross_fixture_scenarios=3,raw_dataclasses_compatible=3)
report={'status':'PASS' if not errors else 'FAIL','contract_status':'DRAFT','contract_version':manifest['contract_version'],'counts':counts,'errors':errors,'tools':{x:importlib.metadata.version(x) for x in ['openapi-spec-validator','jsonschema','referencing','PyYAML']},'limitations':['No backend, real provider, auth, AWS, browser or runtime integration tested.','Schemas cannot prove membership, quota, idempotency/lease transactions, URL expiry, provider readiness or dynamic config application.']}
Path('/private/tmp/ct02-validation-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if not errors else 1)
```

## JavaScript: parser AsyncAPI

```javascript
const fs = require('fs');
const {Parser} = require('/private/tmp/ct02-asyncapi-validation/node_modules/@asyncapi/parser');
(async () => {
  const file = require('path').resolve('contracts/asyncapi.yaml');
  const {document, diagnostics} = await new Parser().parse(fs.readFileSync(file, 'utf8'), {source: file});
  const result = {document_created: !!document, errors: diagnostics.filter(d => d.severity === 0), warnings: diagnostics.filter(d => d.severity === 1), infos:diagnostics.filter(d=>d.severity>1), diagnostic_count:diagnostics.length};
  fs.writeFileSync('/private/tmp/ct02-asyncapi-result.json',JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
  process.exitCode = (!document || result.errors.length) ? 1 : 0;
})().catch(e=>{console.error(e);process.exitCode=1;});
```
