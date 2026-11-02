"""One real source-model W42 corner preview; same approved sourceglass."""
from pathlib import Path
F=Path(__file__).parent
code=(F/'render_window41_preview.py').read_text().replace("'SM_AP_W41WindowWallR'","'SM_AP_W42WindowWallR'").replace("'SM_AP_W41ShadeFrameR'","'SM_AP_W42ShadeFrameR'").replace("F/'Window41_UnitKits.blend'","F/'Window42_UnitKits.blend'").replace("[('Standing',1.62),('Seated',1.38)]","[('Standing',1.62)]").replace("'Window41_SourcePreview_'","'Window42_SourcePreview_'")
exec(compile(code,str(F/'render_window41_preview.py'),'exec'))
