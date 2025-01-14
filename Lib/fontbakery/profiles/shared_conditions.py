from typing import List
from collections import Counter

from fontbakery.callable import condition
# used to inform get_module_profile whether and how to create a profile
from fontbakery.fonts_profile import profile_factory # NOQA pylint: disable=unused-import,cyclic-import


@condition
def ttFont(font):
  from fontTools.ttLib import TTFont
  return TTFont(font)


@condition
def is_ttf(ttFont):
  return 'glyf' in ttFont


@condition
def are_ttf(ttFonts):
  for f in ttFonts:
    if not is_ttf(f):
      return False
  # otherwise:
  return True


@condition
def is_cff(ttFont):
  return 'CFF ' in ttFont

@condition
def is_cff2(ttFont):
  return 'CFF2' in ttFont

@condition
def ligatures(ttFont):
  all_ligatures = {}
  try:
    if "GSUB" in ttFont and ttFont["GSUB"].table.LookupList:
      for record in ttFont["GSUB"].table.FeatureList.FeatureRecord:
        if record.FeatureTag == 'liga':
          for index in record.Feature.LookupListIndex:
            lookup = ttFont["GSUB"].table.LookupList.Lookup[index]
            for subtable in lookup.SubTable:
              for firstGlyph in subtable.ligatures.keys():
                all_ligatures[firstGlyph] = []
                for lig in subtable.ligatures[firstGlyph]:
                  if lig.Component not in all_ligatures[firstGlyph]:
                    all_ligatures[firstGlyph].append(lig.Component)
    return all_ligatures
  except:
    return -1 # Indicate fontTools-related crash...


@condition
def ligature_glyphs(ttFont):
  all_ligature_glyphs = []
  try:
    if "GSUB" in ttFont and ttFont["GSUB"].table.LookupList:
      for record in ttFont["GSUB"].table.FeatureList.FeatureRecord:
        if record.FeatureTag == 'liga':
          for index in record.Feature.LookupListIndex:
            lookup = ttFont["GSUB"].table.LookupList.Lookup[index]
            for subtable in lookup.SubTable:
              for firstGlyph in subtable.ligatures.keys():
                for lig in subtable.ligatures[firstGlyph]:
                  if lig.LigGlyph not in all_ligature_glyphs:
                    all_ligature_glyphs.append(lig.LigGlyph)
    return all_ligature_glyphs
  except:
    return -1  # Indicate fontTools-related crash...


@condition
def glyph_metrics_stats(ttFont):
  """Returns a dict containing whether the font seems_monospaced,
  what's the maximum glyph width and what's the most common width.

  For a font to be considered monospaced, at least 80% of
  the ascii glyphs must have the same width."""
  glyph_metrics = ttFont['hmtx'].metrics
  ascii_glyph_names = [ttFont.getBestCmap()[c] for c in range(32, 128)
                       if c in ttFont.getBestCmap()]
  ascii_widths = [adv for name, (adv, lsb) in glyph_metrics.items()
                  if name in ascii_glyph_names]
  ascii_width_count = Counter(ascii_widths)
  ascii_most_common_width = ascii_width_count.most_common(1)[0][1]
  seems_monospaced = ascii_most_common_width >= len(ascii_widths) * 0.8

  width_max = max([adv for k, (adv, lsb) in glyph_metrics.items()])
  most_common_width = Counter(glyph_metrics.values()).most_common(1)[0][0][0]
  return {
      "seems_monospaced": seems_monospaced,
      "width_max": width_max,
      "most_common_width": most_common_width,
  }


@condition
def missing_whitespace_chars(ttFont):
  from fontbakery.utils import get_glyph_name
  space = get_glyph_name(ttFont, 0x0020)
  nbsp = get_glyph_name(ttFont, 0x00A0)
  # tab = get_glyph_name(ttFont, 0x0009)

  missing = []
  if space is None: missing.append("0x0020")
  if nbsp is None: missing.append("0x00A0")
  # fonts probably don't need an actual tab char
  # if tab is None: missing.append("0x0009")
  return missing


@condition
def vmetrics(ttFonts):
  from fontbakery.utils import get_bounding_box
  v_metrics = {"ymin": 0, "ymax": 0}
  for ttFont in ttFonts:
    font_ymin, font_ymax = get_bounding_box(ttFont)
    v_metrics["ymin"] = min(font_ymin, v_metrics["ymin"])
    v_metrics["ymax"] = max(font_ymax, v_metrics["ymax"])
  return v_metrics


@condition
def is_variable_font(ttFont):
  return "fvar" in ttFont.keys()


@condition
def slnt_axis(ttFont):
  if "fvar" in ttFont:
    for axis in ttFont["fvar"].axes:
      if axis.axisTag == "slnt":
        return axis


def get_instance_axis_value(ttFont, instance_name, axis_tag):
  if not is_variable_font(ttFont):
    return None

  instance = None
  for i in ttFont["fvar"].instances:
    name = ttFont["name"].getDebugName(i.subfamilyNameID)
    if name == instance_name:
      instance = i
      break

  if instance:
    for axis in ttFont["fvar"].axes:
      if axis.axisTag == axis_tag:
        return instance.coordinates[axis_tag]


@condition
def regular_wght_coord(ttFont):
  return get_instance_axis_value(ttFont, "Regular", "wght")


@condition
def bold_wght_coord(ttFont):
  return get_instance_axis_value(ttFont, "Bold", "wght")


@condition
def regular_wdth_coord(ttFont):
  return get_instance_axis_value(ttFont, "Regular", "wdth")


@condition
def regular_slnt_coord(ttFont):
  return get_instance_axis_value(ttFont, "Regular", "slnt")


@condition
def regular_ital_coord(ttFont):
  return get_instance_axis_value(ttFont, "Regular", "ital")


@condition
def regular_opsz_coord(ttFont):
  return get_instance_axis_value(ttFont, "Regular", "opsz")


@condition
def vtt_talk_sources(ttFont) -> List[str]:
  """Return the tags of VTT source tables found in a font."""
  VTT_SOURCE_TABLES = {'TSI0', 'TSI1', 'TSI2', 'TSI3', 'TSI5'}
  tables_found = [tag for tag in ttFont.keys() if tag in VTT_SOURCE_TABLES]
  return tables_found
