#Import arcpy
import arcpy
import os

#Input City
city_name = arcpy.GetParameterAsText(0)

#Set data paths
municipalities_fc = r"C:\GEOG3700\FinalProject_Bryner\data_inputs\Municipalities.shp"
muni_field = "NAME"

schools_fc = r"C:\GEOG3700\FinalProject_Bryner\data_inputs\Schools_PreKto12.shp"
libraries_fc = r"C:\GEOG3700\FinalProject_Bryner\data_inputs\PublicLibraries.shp"
fire_fc = r"C:\GEOG3700\FinalProject_Bryner\data_inputs\FireStations.shp"
parks_fc = r"C:\GEOG3700\FinalProject_Bryner\data_inputs\ParksLocal.shp"
address_fc = r"C:\GEOG3700\FinalProject_Bryner\data_inputs\AddressPoints.shp"

#Set output
aprx = arcpy.mp.ArcGISProject("CURRENT")
gdb = aprx.defaultGeodatabase
out_name = "BestSites_" + city_name.replace(" ", "_")
out_fc = os.path.join(gdb, out_name)

arcpy.env.overwriteOutput = True
scratch = arcpy.env.scratchGDB

#Select municipality
safe_city = city_name.replace("'", "''")
sql = f"{muni_field} = '{safe_city}'"

city_boundary = os.path.join(scratch, "city_boundary")
arcpy.Select_analysis(municipalities_fc, city_boundary, sql)

#Clip data based off of selected municipality
def clip(fc, name):
    out = os.path.join(scratch, name)
    arcpy.Clip_analysis(fc, city_boundary, out)
    return out

schools_c = clip(schools_fc, "schools_c")
libraries_c = clip(libraries_fc, "libraries_c")
fire_c = clip(fire_fc, "fire_c")
parks_c = clip(parks_fc, "parks_c")
address_c = clip(address_fc, "address_c")

#Calculate distance and scores
dist_fields = [
    ("dist_school", schools_c),
    ("dist_library", libraries_c),
    ("dist_fire", fire_c),
    ("dist_park", parks_c)
]

for field, near_fc in dist_fields:
    arcpy.AddField_management(address_c, field, "DOUBLE")
    arcpy.Near_analysis(address_c, near_fc)
    arcpy.CalculateField_management(address_c, field, "!NEAR_DIST!", "PYTHON3")

arcpy.AddField_management(address_c, "score", "DOUBLE")

score_expr = (
    "(10000 - !dist_school!) + "
    "(10000 - !dist_library!) + "
    "(10000 - !dist_fire!) + "
    "(10000 - !dist_park!)"
)

arcpy.CalculateField_management(address_c, "score", score_expr, "PYTHON3")

#Select 20 best address points based off of scores
sorted_fc = os.path.join(scratch, "sorted_fc")
arcpy.Sort_management(address_c, sorted_fc, [["score", "DESCENDING"]])

top20 = os.path.join(scratch, "top20")
arcpy.Select_analysis(sorted_fc, top20, "OBJECTID <= 20")

arcpy.CopyFeatures_management(top20, out_fc)

#Add layer to map
m = aprx.listMaps()[0]
m.addDataFromPath(out_fc)
aprx.save()

