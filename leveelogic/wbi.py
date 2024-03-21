from enum import IntEnum


class SchadeFactorMode(IntEnum):
    SIGNALERING = 0
    ONDERGRENS = 1


class FaalkansruimteToetsspoor(IntEnum):
    HTKW = 0
    STPH = 1
    STBI = 2
    GEBU = 3
    OVERIGE_BEKLEDINGEN_BUITENTALUD = 4
    BSKW = 5
    PKW = 6
    STKWp = 7
    DA = 8
    OVERIG = 9


FaalkansruimteFactorDijkenEnDammen = {
    FaalkansruimteToetsspoor.HTKW: 0.24,
    FaalkansruimteToetsspoor.STPH: 0.24,
    FaalkansruimteToetsspoor.STBI: 0.04,
    FaalkansruimteToetsspoor.GEBU: 0.05,
    FaalkansruimteToetsspoor.OVERIGE_BEKLEDINGEN_BUITENTALUD: 0.05,
    FaalkansruimteToetsspoor.BSKW: 0.04,
    FaalkansruimteToetsspoor.PKW: 0.02,
    FaalkansruimteToetsspoor.STKWP: 0.02,
    FaalkansruimteToetsspoor.DA: 0.0,
    FaalkansruimteToetsspoor.OVERIG: 0.3,
}


def schadefactor(
    schadefactor_mode: SchadeFactorMode,
    faalkansruimte_toetsspoor: FaalkansruimteToetsspoor,
    faalkans_signalering: int,  # 1:xxx jaar
    faalkans_ondergrens: int,  # 1:xxx jaar
    lengte_factor: int,
    lengte_dijkvak: int,
    rep_lengte_doorsnede: int,
    lengte_effect_factor: float,
    kans_op_falen_gegeven_instabiliteit: float,  # 1.0 voor STBI, 0.1 voor STBU
):
    f = FaalkansruimteFactorDijkenEnDammen[faalkansruimte_toetsspoor]
    p_eis_dsn_sig = (f * 1 / faalkans_signalering) / (
        (1 + (lengte_factor * lengte_dijkvak) / rep_lengte_doorsnede)
        * kans_op_falen_gegeven_instabiliteit
    )
    p_eis_dsn_ond = (f * 1 / faalkans_ondergrens) / (
        (1 + (lengte_factor * lengte_dijkvak) / rep_lengte_doorsnede)
        * kans_op_falen_gegeven_instabiliteit
    )
    beta_eis_dsn_sig = 1.0
    # TODO
