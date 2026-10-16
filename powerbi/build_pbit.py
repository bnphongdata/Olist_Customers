import zipfile
import json
import os

bim_path = r'd:\Olist Customers\powerbi\model.bim'
report_json_path = r'd:\Olist Customers\powerbi\Olist_Analytics.Report\report.json'
pbit_path = r'd:\Olist Customers\powerbi\Olist_Analytics.pbit'

with open(bim_path, 'r', encoding='utf-8') as f:
    bim_content = f.read()

with open(report_json_path, 'r', encoding='utf-8') as f:
    report_content = f.read()

content_types_xml = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
    '  <Default Extension="json" ContentType="" />\n'
    '  <Override PartName="/Report/Layout" ContentType="" />\n'
    '  <Override PartName="/DataModelSchema" ContentType="" />\n'
    '  <Override PartName="/Settings" ContentType="" />\n'
    '  <Override PartName="/Version" ContentType="" />\n'
    '</Types>'
)

settings_json = json.dumps({'version': '5.55'}, indent=2)
version_str = '2.149.1429.0'

with zipfile.ZipFile(pbit_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('[Content_Types].xml', content_types_xml.encode('utf-8'))
    zf.writestr('Version', version_str.encode('utf-16-le'))
    zf.writestr('Settings', settings_json.encode('utf-16-le'))
    zf.writestr('DataModelSchema', bim_content.encode('utf-16-le'))
    zf.writestr('Report/Layout', report_content.encode('utf-16-le'))

print('PBIT_SUCCESS:', pbit_path, 'Bytes:', os.path.getsize(pbit_path))
