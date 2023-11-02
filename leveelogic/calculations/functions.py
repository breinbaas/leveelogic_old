from statistics import NormalDist


def sf_to_beta(sf: float, model_factor: float):
    """Generate reliability index from safety factor

    Args:
        sf (float): Safety factor (without model factor)
        model_factor (float): Model factor

        Bishop: 1.11
        LiftVan: 1.06
        Spencer: 1.07

        Source: sh-macrostabiliteit-v4-28-mei-2021.pdf Table 2.4 (WBI)

    Returns:
        _type_: Beta (reliability index)
    """
    return (sf / model_factor - 0.41) / 0.15


def beta_to_pf(beta: float) -> float:
    """Convert reliability index to faalkans

    Source: handreiking_faalkansanalyses_macrostabiliteit_-_definitief - kader 2.1 (WBI)

    Args:
        beta (float): reliability index

    Returns:
        float: faalkans
    """
    a = NormalDist().cdf(-1 * beta)
    return NormalDist().cdf(x=-beta)


def pf_to_beta(pf: float) -> float:
    """Convert faalkans to reliability index

    Source: handreiking_faalkansanalyses_macrostabiliteit_-_definitief - kader 2.1 (WBI)

    Args:
        pf (float): faalkans

    Returns:
        float: reliability index
    """
    return NormalDist().inv_cdf(1 - pf)
