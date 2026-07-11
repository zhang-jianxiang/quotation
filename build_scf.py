import json, base64, zlib, os, re

SECRET = 'genset2024secret'

def xor_encrypt(data_str, key):
    return ''.join(chr(ord(data_str[i]) ^ ord(key[i % len(key)])) for i in range(len(data_str)))

def compress(data_str):
    return base64.b64encode(zlib.compress(data_str.encode('utf-8'))).decode('ascii')

def encrypt_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        data_str = json.dumps(data, ensure_ascii=False)
        compressed = compress(data_str)
        encrypted = xor_encrypt(compressed, SECRET)
        return base64.b64encode(encrypted.encode('latin1')).decode('ascii')

# Root directory
ROOT = r'd:\kc\code\quotation'

genset_enc = encrypt_file(os.path.join(ROOT, 'genset_price_catalog.json'))
alt_enc = encrypt_file(os.path.join(ROOT, 'alternator_price_catalog.json'))
canopy_enc = encrypt_file(os.path.join(ROOT, 'canopy_price_catalog.json'))

# Load the generated HTML
with open(os.path.join(ROOT, 'genset_price_calculator.html'), 'r', encoding='utf-8') as f:
    html_content = f.read()

# Prepare for JS embedding
# We need to adjust the HTML content slightly if it expects a local file (LOGO.webp)
# But in scf, we might want to inline it or just let it fail if it's not critical.
# The current scf/index.js doesn't seem to have the logo embedded.
# Let's check if we should embed the logo.
with open(os.path.join(ROOT, 'LOGO.webp'), 'rb') as f:
    logo_enc = base64.b64encode(f.read()).decode('ascii')
    html_content = html_content.replace('src="LOGO.webp"', f'src="data:image/webp;base64,{logo_enc}"')

# Update index.js
index_path = os.path.join(ROOT, 'scf_deploy', 'index.js')
with open(index_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace DATA strings
content = re.sub(r"genset: '.*?'", f"genset: '{genset_enc}'", content)
content = re.sub(r"alternator: '.*?'", f"alternator: '{alt_enc}'", content)
content = re.sub(r"canopy: '.*?'", f"canopy: '{canopy_enc}'", content)

# Replace HTML_CONTENT
# Use a placeholder or regex. The HTML_CONTENT is at the end.
# We'll use a more robust way to replace the HTML_CONTENT variable.
# It starts with 'const HTML_CONTENT = `\n' and ends with '`;' at the very end.
start_marker = 'const HTML_CONTENT = `'
end_marker = '`;'
start_idx = content.find(start_marker)
if start_idx != -1:
    # Find the end marker after the start marker
    # Note: this assumes the HTML doesn't contain ` closing it early.
    # Our HTML might contain backticks in JS.
    # We should escape backticks in the HTML content if we use backticks for the template literal.
    escaped_html = html_content.replace('`', '\\`').replace('$', '\\$')
    new_content = content[:start_idx + len(start_marker)] + escaped_html + end_marker
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {index_path} successfully.")
else:
    print("Could not find HTML_CONTENT marker in index.js")
