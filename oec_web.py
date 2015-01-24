import xml.etree.ElementTree as ET
import glob
import urllib
from numberformat import renderFloat, notAvailableString
from flask import Flask, abort, render_template


OEC_PATH = "open_exoplanet_catalogue/"

print "Parsing OEC ..."
systems = []
planets = []
stars = []
binaries = []
xmlPairs = {}

# Loop over all files and  create new data
for filename in glob.glob(OEC_PATH + "systems/*.xml"):
    # Open file
    f = open(filename, 'rt')
    # Try to parse file
    try:
        root = ET.parse(f).getroot()
        systems += root
        for p in root.findall(".//planet"):
            planets.append((root,p))
            name = p.find("./name").text
            xmlPairs[name] = (root,p)
        stars += root.findall(".//star")
        binaries += root.findall(".//binary")
    except ET.ParseError as error:
        print '{}, {}'.format(filename, error)
        continue
    finally:
        f.close()

print "Parsing OEC done"

""" Array of title of propoerties """
title = {
    "name":                         "Primary planet name",
    "alternativenames":             "Alternative planet names",
    "systemname":                   "Primary system name",
    "systemalternativenames":       "Alternative system names",
    "distance":                     "Distance [parsec]",
    "distancelightyears":           "Distance [lightyears]",
    "numberofplanets":              "Number of planets in system",
    "numberofstars":                "Number of stars in system",
    "rightascension":               "Right ascension",
    "declination":                  "Declination",
    "image":                        "Image",
    "period":                       "Orbital period [days]",
    "semimajoraxis":                "Semi-major axis [AU]",
    "eccentricity":                 "Eccentricity",
    "temperature":                  "Equilibtrium temperature [K]",
    "lists":                        "Lists",
    "description":                  "Description",
    "discoveryyear":                "Discovery year",
    "discoverymethod":              "Discovery method",
    "lastupdate":                   "Last updated [yy/mm/dd]",
    "mass":                         "Mass [M<sub>jup</sub>]",
    "radius":                       "Radius [R<sub>jup</sub>]",
    "massEarth":                    "Mass [M<sub>earth</sub>]",
    "radiusEarth":                  "Radius [R<sub>earth</sub>]"
}

def render(xmlPair,type):
    system, planet = xmlPair
    if type=="numberofplanets":
        return "%d"%len(system.findall(".//planet"))
    if type=="numberofstars":
        return "%d"%len(system.findall(".//star"))
    if type=="distance":
        return renderFloat(system.find("./distance"))
    if type=="distancelightyears":
        return renderFloat(system.find("./distance"),3.2615638)
    if type=="massEarth":
        return renderFloat(planet.find("./mass"),317.8942)
    if type=="radiusEarth":
        return renderFloat(planet.find("./radius"),10.973299)
    # Text based object
    if type=="rightascension":
        return system.find("./rightascension").text
    if type=="declination":
        return system.find("./declination").text
    if type=="image":
        return planet.find("./image").text
    if type=="description":
        return planet.find("./description").text
    if type=="name":
        return planet.find("./name").text
    if type=="discoveryyear":
        return planet.find("./discoveryyear").text
    if type=="discoverymethod":
        return planet.find("./discoverymethod").text
    if type=="lastupdate":
        return planet.find("./lastupdate").text
    if type=="systemname":
        return system.find("./name").text
    if type=="alternativenames":
        alternativenames = notAvailableString 
        names = planet.findall("./name")
        for i,name in enumerate(names[1:]):
            if i==0:
                alternativenames = ""
            else:
                alternativenames += ", "
            alternativenames += name.text
        return alternativenames
    if type=="systemalternativenames":
        systemalternativenames = notAvailableString 
        systemnames = system.findall("./name")
        for i,name in enumerate(systemnames[1:]):
            if i==0:
                systemalternativenames = ""
            else:
                systemalternativenames += ", "
            systemalternativenames += name.text
        return systemalternativenames
    if type=="lists":
        lists = notAvailableString 
        ls = planet.findall("./list")
        for i,l in enumerate(ls):
            if i==0:
                lists = ""
            else:
                lists += "; "
            lists += l.text
        return lists
    # Default: just search for the property in the planet xml. 
    return renderFloat(planet.find("./"+type))

app = Flask(__name__)
@app.route('/')
@app.route('/index.html')
def main_page():
    return render_template("index.html")

@app.route('/systems/')
def systems():
    p = []
    fields = ["name","mass","radius","massEarth","radiusEarth","numberofplanets","numberofstars"]
    for xmlPair in planets:
        system,planet = xmlPair
        d = {}
        name = render(xmlPair,"name")
        d["fields"] = ["<a href=\"/planet/%s/\">%s</a>"%(urllib.quote(name),name)]
        for field in fields[1:]:
            d["fields"].append(render(xmlPair,field))
        p.append(d)
    return render_template("systems.html",columns=[title[field] for field in fields],planets=p)


@app.route('/planet/<planetname>')
@app.route('/planet/<planetname>/')
def hello_planet(planetname):
    xmlPair = xmlPairs[planetname]
    system,planet = xmlPair
    systemname = render(xmlPair,"systemname")
    systemcategory = ""
    if len(system.findall(".//planet"))==1:
        systemcategory += "The planetary system "+systemname+" hosts at least one planet. "
    elif len(system.findall(".//planet"))>1:
        systemcategory += "The planetary system "+systemname+" hosts at least %d planets. " % len(system.findall(".//planet"))
    
    if len(system.findall(".//star"))>1:
        systemcategory += "Note that the system is a multiple star system. It hosts at least %d stellar components. "% len(system.findall(".//star"))
    #	$(".systembinarytext").html("Note that <span class=\"systemname\"></span> is binary system. The list can be used to infer which planet is orbiting which star and whether it is a S- or P-type orbit.");
    #}else{
    #	$(".systembinarytext").html("<span class=\"systemname\"></span> is not binary system, so the architecture is rather simple. ");
    #}
    elif len(system.findall(".//star"))==0:
        systemcategory += "The planet is a so called orphan planet and not associated with any star. "

    systemtable = []
    for row in ["systemname","systemalternativenames","rightascension","declination","distance","distancelightyears","numberofstars","numberofplanets"]:
        systemtable.append((title[row],render(xmlPair,row)))
    
    planettable = []
    for row in ["name","alternativenames","description","lists","mass","massEarth","radius","radiusEarth","period","semimajoraxis","eccentricity","temperature","discoverymethod","discoveryyear","lastupdate"]:
        planettable.append((title[row],render(xmlPair,row)))

    return render_template("planet.html",
        planetname=planetname,
        systemname=systemname,
        systemtable=systemtable,
        planettable=planettable,
        systemcategory=systemcategory,
        )
    #abort(404)


if __name__ == '__main__':
    app.run(debug=True)