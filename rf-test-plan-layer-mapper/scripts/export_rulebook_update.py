import argparse, json
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('--delta', required=True); ap.add_argument('--output', required=True); args=ap.parse_args()
data=json.loads(Path(args.delta).read_text(encoding='utf-8'))
changes=data.get('changes',[]); style=data.get('style','UNKNOWN'); sheet=data.get('sheet','')
lines=['# Mapping Learning Note','',f'- Workbook style: **{style}**',f'- Sheet: **{sheet}**',f'- Total changed mapping cells: **{len(changes)}**','','## Raw deltas','']
for ch in changes[:5000]:
    lines.append(f"- Source row {ch.get('row')} -> target row {ch.get('target_row')} col {ch.get('column')}: `{ch.get('new','')}`")
Path(args.output).write_text('\n'.join(lines), encoding='utf-8'); print(args.output)
