from pathlib import Path
from typing import List, Tuple
from pyproj import Transformer
from shapely.geometry import Point, LineString, MultiPoint
import re
from matplotlib.pyplot import Figure
from matplotlib.patches import Polygon as MPolygon

from .settings import (
    nen5104_sand_dict,
    nen5104_main_soilname_dict,
    UNHANDLED_SOILCODE_NAME,
    nen5104_addition_names_dict,
    nen5104_addition_amount_dict,
    nen5104_sand_color_dict,
    nen5104_main_soilcolor_dict,
    nen5104_addition_color_dict,
)


def hex_color_to_rgb_tuple(s: str) -> Tuple[float, float, float]:
    """Convert a heximal color string to RGB tuple

    Args:
        s (str): The string like 0xrrggbb

    Returns:
        Tuple[float, float, float]: The RGB values
    """
    r = int(f"0x{s[1:3]}", 0)
    g = int(f"0x{s[3:5]}", 0)
    b = int(f"0x{s[5:7]}", 0)
    return (r, g, b)


def case_insensitive_glob(filepath: str, fileextension: str) -> List[Path]:
    """Find files in given path with given file extension (case insensitive)

    Arguments:
        filepath (str): path to files
        fileextension (str): file extension to use as a filter (example .gef or .csv)

    Returns:
        List(str): list of files
    """
    p = Path(filepath)
    result = []
    for filename in p.glob("**/*"):
        if str(filename.suffix).lower() == fileextension.lower():
            result.append(filename.absolute())
    return result


def xy_to_latlon(x: float, y: float, epsg: int = 28992) -> Tuple[float, float]:
    """Convert coordinates from the given epsg to latitude longitude coordinate

    Arguments:
        x (float): x coordinate
        y (float): y coordinate
        epsg (int): EPSG according to https://epsg.io/, defaults to 28992 (Rijksdriehoek coordinaten)

    Returns:
         Tuple[float, float]: latitude, longitude rounded to 6 decimals
    """
    if epsg == 4326:
        return x, y

    try:
        transformer = Transformer.from_crs(epsg, 4326)
        lat, lon = transformer.transform(x, y)
    except Exception as e:
        raise e

    return (round(lat, 6), round(lon, 6))


def latlon_to_xy(lat: float, lon: float, epsg=28992) -> Tuple[float, float]:
    """Convert latitude longitude coordinate to given epsg

    Arguments:
        lat (float): latitude
        lon (float): longitude
        epsg (int): EPSG according to https://epsg.io/, defaults to 28992 (Rijksdriehoek coordinaten)

    Returns:
         Tuple[float, float]: x, y in given epsg coordinate system
    """
    try:
        transformer = Transformer.from_crs(4326, epsg)
        x, y = transformer.transform(lat, lon)
    except Exception as e:
        raise e

    return (x, y)


def soilcode_to_stabparameters(main, sand, adds):
    add = None
    if len(adds) > 0:
        add = adds[0]

    if main == "V":
        if add is None:
            return (10.0, 10.0, 2.0, 15.0, 15.0)

        if add[0] in ["k", "s", "z"]:
            if int(add[1]) == 1:
                return (10.5, 10.5, 1.0, 17.5, 17.5)
            else:
                return (11.0, 11.0, 2.0, 17.5, 17.5)
        elif add[0] == "g":
            return (11.0, 11.0, 2.0, 17.5, 17.5)
        elif add[0] == "h":
            if int(add[1]) < 1:
                return (10.5, 10.5, 1.0, 15.0, 15.0)
            else:
                return (10.0, 10.0, 0.5, 17.5, 17.5)
    elif main == "K":
        if add is None:
            return (14.0, 14.0, 2.0, 22.0, 22.0)

        if add[0] in ["g", "z"]:
            if int(add[1]) <= 2:
                return (15.0, 15.0, 2.0, 25.0, 25.0)
            elif int(add[1]) == 3:
                return (16.0, 16.0, 3.0, 25.0, 25.0)
            elif int(add[1]) >= 4:
                return (17.0, 17.0, 1.0, 27.5, 27.5)
        elif add[0] == "s":
            if int(add[1]) <= 2:
                return (14.0, 14.0, 2.0, 25, 25)
            elif int(add[1]) == 3:
                return (15.0, 15.0, 2.0, 25, 25)
            elif int(add[1]) >= 4:
                return (16.0, 16.0, 1.0, 27.5, 27.5)
        elif add[0] == "h":
            if int(add[1]) <= 2:
                return (14.0, 14.0, 3.0, 22, 22)
            elif int(add[1]) == 3:
                return (13.0, 13.0, 3.5, 20, 20)
            elif int(add[1]) >= 4:
                return (12.0, 12.0, 4.0, 18, 18)
    elif main == "Z":
        if sand in ["ZUF", "ZZF"]:
            return (17.0, 19.0, 0, 30, 30)
        elif sand in ["ZMG", "ZZG", "ZUG"]:
            return (19.0, 21.0, 0, 35, 35)
        elif sand == "ZMF":
            return (18.0, 20.0, 0, 32.5, 32.5)
        else:
            return (17.0, 19.0, 0, 30, 30)
    elif main == "G":
        return (20.0, 22.0, 0, 30, 30)
    elif main == "L":
        return (15.0, 15.0, 2, 25, 25)
    else:
        return (0.0, 0.0, 0, 0, 0)


def soilcode_as_info(soilcode):
    main = soilcode[0]
    sand = ""
    adds = []

    if main == "Z":
        for k in nen5104_sand_dict.keys():
            if soilcode.find(k) > -1:
                sand = k
                soilcode = soilcode.replace(sand, "")
                break
            else:  # assume that it is ZMF so we can at least get some automated soil parameters and color
                sand = "ZMF"

    if not main in nen5104_main_soilname_dict.keys():
        print(f"unhandled soilcode {soilcode}")
        return UNHANDLED_SOILCODE_NAME, "", []

    adds = re.findall("\w\d", soilcode[1:])

    validadds = [add for add in adds if add[0] in nen5104_addition_names_dict.keys()]
    validadds = [
        add for add in validadds if add[1] in nen5104_addition_amount_dict.keys()
    ]

    return main, sand, validadds


def soilcode_to_parameters(soilcode: str) -> str:
    if soilcode == UNHANDLED_SOILCODE_NAME:
        return {
            "color": "#696969",
            "y_dry": 0.0,
            "y_sat": 0.0,
            "cohesion": 0.0,
            "friction_angle": 0.0,
        }

    try:
        main, sand, adds = soilcode_as_info(soilcode)
        color = ingredients_to_color(main, sand, adds)
        params = soilcode_to_stabparameters(main, sand, adds)
        return {
            "color": color,
            "y_dry": params[0],
            "y_sat": params[1],
            "cohesion": params[2],
            "friction_angle": params[3],
        }
    except:
        print(f"Unhandled soilcode {soilcode}, getting default parameters")
        return {
            "color": "#696969",
            "y_dry": 0.0,
            "y_sat": 0.0,
            "cohesion": 0.0,
            "friction_angle": 0.0,
        }


def ingredients_to_color(main, sand, adds) -> str:
    fg, bg = "#000000", "#000000"

    if len(sand) > 0:
        fg = nen5104_sand_color_dict[sand]
    else:
        fg = nen5104_main_soilcolor_dict[main]

    maxadd = -1
    for add in adds:
        if int(add[1]) > maxadd:
            maxadd = int(add[1])
            if maxadd > 4:
                maxadd = 4
            bg = nen5104_addition_color_dict[add[0]]

    if bg == "#000000":
        return fg
    else:
        alpha_bg = maxadd / 3 * 0.5
        alpha_fg = 1 - alpha_bg

        fgt = tuple(int(fg.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4))
        bgt = tuple(int(bg.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4))

        alpha_r = 1 - (1 - alpha_fg) * (1 - alpha_bg)
        color = [
            round(
                (
                    fgt[i] * alpha_fg / alpha_r
                    + bgt[i] * alpha_bg * (1 - alpha_fg) / alpha_r
                )
                * 255
            )
            for i in range(3)
        ]
        color = "#%02x%02x%02x" % (color[0], color[1], color[2])

        return color


def longcode_to_shortcode(soilcode: str) -> str:
    """
    Convert a longcode to a shortcode

    Args:
        soilcode (str): The current soilcode

    Returns:
        str: shortcode
    """
    try:
        main, sand, adds = soilcode_as_info(soilcode)
        code = main
        if len(sand) > 0:
            code += sand
        for add in adds:
            code += add
        return code
    except:
        return UNHANDLED_SOILCODE_NAME


def get_key(dict, val):
    for key, value in dict.items():
        if val == value:
            return key
    raise ValueError(f"Unknown value '{val}' for the given dict.")


def sti_geometry_helper(top: List[int], bottom: List[int]) -> List[int]:
    polyline = top + bottom[::-1]
    result = []

    # remove from the beginning and end if they are the same but save the last removed idx
    for i in range(len(polyline)):
        if polyline[0] == polyline[-1]:
            result = [polyline[0]]
            polyline.pop(0)
            polyline.pop(-1)
        else:
            if len(result) > 0:
                for p in polyline:
                    if p != polyline[-1]:
                        result.append(p)
                    else:
                        result.append(p)
                        break
                return result

    # no result, lets try it the other way
    polyline = top[::-1] + bottom
    for i in range(len(polyline)):
        if polyline[0] == polyline[-1]:
            result = [polyline[0]]
            polyline.pop(0)
            polyline.pop(-1)
        else:
            if len(result) > 0:
                for p in polyline:
                    if p != polyline[-1]:
                        result.append(p)
                    else:
                        result.append(p)
                        break
                return result[::-1]

    # no result, all unique points
    return top + bottom[::-1]


def line_polyline_intersections(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    polyline_points: List[Tuple[float, float]],
) -> List[Tuple[float, float]]:
    """Find the intersections between the line given by x1,y1 x2,y2 and a list of points
    (x,y) describing a polyline

    Returns the intersections sorted on x
    """
    surface_line = LineString(polyline_points)
    pp_line = LineString([(x1, y1), (x2, y2)])

    intersections = pp_line.intersection(surface_line)

    if type(intersections) == Point:
        return [(round(intersections.x, 3), round(intersections.y, 3))]
    elif type(intersections) == MultiPoint:
        return sorted(
            [(round(p.x, 3), round(p.y, 3)) for p in intersections.geoms],
            key=lambda x: x[0],
        )
    else:
        NotImplementedError(
            f"DEV > getting a intersection result that is not of type Point or Multipoint but {type(intersections)}"
        )


def polyline_polyline_intersections(
    points_line1: List[Tuple[float, float]],
    points_line2: List[Tuple[float, float]],
):
    result = []
    ls1 = LineString(points_line1)
    ls2 = LineString(points_line2)
    intersections = ls1.intersection(ls2)

    if intersections.is_empty:
        final_result = []
    elif type(intersections) == MultiPoint:
        result = [(g.x, g.y) for g in intersections.geoms]
    elif type(intersections) == Point:
        x, y = intersections.coords.xy
        result.append((x[0], y[0]))
    elif intersections.is_empty:
        return []
    else:
        raise ValueError(f"Unimplemented intersection type '{type(intersections)}'")

    # do not include points that are on line1 or line2
    final_result = [p for p in result if not p in points_line1 or p in points_line2]

    if len(final_result) == 0:
        return []

    return sorted(final_result, key=lambda x: x[0])


def plot_soilpolygons(
    spg,
    soilcollection,
    size_x: float = 10,
    size_y: float = 6,
):
    fig = Figure(figsize=(size_x, size_y))
    ax = fig.add_subplot()

    xs, ys = [], []

    for sp in spg:
        xs += [p[0] for p in sp.points]
        ys += [p[1] for p in sp.points]
        try:
            color = soilcollection.get(sp.soilcode).color
        except Exception as e:
            raise ValueError(
                f"Could not find a soil definition for soil code '{sp.soilcode}'"
            )

        pg = MPolygon(
            sp.points,
            color=color,
            alpha=0.7,
        )
        ax.add_patch(pg)
        # ax.text(sp.left, soillayer.bottom, soillayer.soilcode)

    ax.set_xlim(min(xs), max(xs))
    ax.set_ylim(min(ys), max(ys))

    return fig
