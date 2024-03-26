import dtcc
from pathlib import Path

data_directory = Path(__file__).parent / ".." / "data" / "cityjson"

# city = dtcc.load_city(data_directory / "DA13_3D_Buildings_Merged.city.json")
city = dtcc.load_city(data_directory / "DenHaag_01.city.json")
city.view()
