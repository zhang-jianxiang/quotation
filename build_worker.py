import json, base64, zlib, re, os

SECRET = 'genset2024secret'

def xor_encrypt(data_str, key):
    return ''.join(chr(ord(data_str[i]) ^ ord(key[i % len(key)])) for i in range(len(data_str)))

def compress(data_str):
    return base64.b64encode(zlib.compress(data_str.encode('utf-8'))).decode('ascii')

# Data processing
with open('D:/kc/code/quotation/web/genset_price_catalog.json', 'r', encoding='utf-8') as f:
    genset_enc = base64.b64encode(xor_encrypt(compress(json.dumps(json.load(f), ensure_ascii=False)), SECRET).encode('latin1')).decode('ascii')
with open('D:/kc/code/quotation/web/alternator_price_catalog.json', 'r', encoding='utf-8') as f:
    alt_enc = base64.b64encode(xor_encrypt(compress(json.dumps(json.load(f), ensure_ascii=False)), SECRET).encode('latin1')).decode('ascii')
with open('D:/kc/code/quotation/web/canopy_price_catalog.json', 'r', encoding='utf-8') as f:
    canopy_enc = base64.b64encode(xor_encrypt(compress(json.dumps(json.load(f), ensure_ascii=False)), SECRET).encode('latin1')).decode('ascii')

# Save data to separate files
data_dir = 'D:/kc/code/quotation/web_worker/data'
os.makedirs(data_dir, exist_ok=True)

with open(f'{data_dir}/genset.txt', 'w', encoding='utf-8') as f: f.write(genset_enc)
with open(f'{data_dir}/alternator.txt', 'w', encoding='utf-8') as f: f.write(alt_enc)
with open(f'{data_dir}/canopy.txt', 'w', encoding='utf-8') as f: f.write(canopy_enc)

# Load and embed logo
logo_path = 'D:/kc/code/quotation/LOGO.webp'
if os.path.exists(logo_path):
    with open(logo_path, 'rb') as f:
        logo_enc = base64.b64encode(f.read()).decode('ascii')
    logo_data_uri = f'data:image/webp;base64,{logo_enc}'
else:
    logo_data_uri = 'LOGO.webp'

# Read HTML
with open('D:/kc/code/quotation/web_worker/index.html', 'r', encoding='utf-8') as f:
    html_content = f.read().replace('src="LOGO.webp"', f'src="{logo_data_uri}"')

# Escape HTML for JS template literal
html_escaped = html_content.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

# Build refactored worker index.js (LITE)
worker_js = f"""const SECRET = 'genset2024secret';
const HTML = `{html_escaped}`;

export default {{
  async fetch(request, env) {{
    const url = new URL(request.url);
    
    // API Endpoints using KV storage
    if (url.pathname === '/api/genset') {{
      const data = await env.DATA_KV.get('genset');
      return new Response(data || 'Data not found in KV', {{ 
        status: data ? 200 : 404,
        headers: {{ 'Content-Type': 'text/plain' }} 
      }});
    }}
    if (url.pathname === '/api/alternator') {{
      const data = await env.DATA_KV.get('alternator');
      return new Response(data || 'Data not found in KV', {{ 
        status: data ? 200 : 404,
        headers: {{ 'Content-Type': 'text/plain' }} 
      }});
    }}
    if (url.pathname === '/api/canopy') {{
      const data = await env.DATA_KV.get('canopy');
      return new Response(data || 'Data not found in KV', {{ 
        status: data ? 200 : 404,
        headers: {{ 'Content-Type': 'text/plain' }} 
      }});
    }}

    // Increment and serve visit count
    let count = parseInt(await env.DATA_KV.get('visit_count') || '0') + 1;
    await env.DATA_KV.put('visit_count', count.toString());

    // Fallback to serving the HTML
    const body = HTML.replace('__VISIT_COUNT__', count.toString());
    return new Response(body, {{ headers: {{ 'Content-Type': 'text/html; charset=utf-8' }} }});
  }}
}};
"""

with open('D:/kc/code/quotation/web_worker/index.js', 'w', encoding='utf-8') as f:
    f.write(worker_js)

print(f'Worker JS generated: {len(worker_js)} bytes')
print(f'Data files saved to: {data_dir}')
print("\n--- NEXT STEPS ---")
print("1. Create KV namespace: npx wrangler kv:namespace create DATA_KV")
print("2. Add the binding to wrangler.toml")
print("3. Upload data to KV:")
print(f"   npx wrangler kv:key put --binding=DATA_KV 'genset' {data_dir}/genset.txt --path")
print(f"   npx wrangler kv:key put --binding=DATA_KV 'alternator' {data_dir}/alternator.txt --path")
print(f"   npx wrangler kv:key put --binding=DATA_KV 'canopy' {data_dir}/canopy.txt --path")
print("4. Deploy: npx wrangler deploy")

