from copy import deepcopy
from geolib.geometry import Point
from typing import List, Tuple

from ..dstability import DStability
from .algorithm import Algorithm
from ...helpers import polyline_polyline_intersections
from ...geometry.characteristic_point import CharacteristicPointType


class AlgorithmMirror(Algorithm):
    def _check_input(self):
        pass

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        # gemoetries
        for geom in ds.model.datastructure.geometries:
            for layer in geom.Layers:
                for point in layer.Points:
                    point.X = ds.right - (point.X - ds.left)

        # loads
        for loads in ds.model.datastructure.loads:
            for load in loads.LineLoads:
                load.Location.X = ds.right - (load.Location.X - ds.left)
            for load in loads.UniformLoads:
                load.End = ds.right - (load.End - ds.left)
                load.Start = ds.right - (load.Start - ds.left)
            for load in loads.Trees:
                load.Location.X = ds.right - (load.Location.X - ds.left)

        for decoration in ds.model.datastructure.decorations:
            for elevation in decoration.Elevations:
                for point in elevation.Points:
                    point.X = ds.right - (point.X - ds.left)
            for excavation in decoration.Excavations:
                for point in excavation.Points:
                    point.X = ds.right - (point.X - ds.left)

        for waternet in ds.model.datastructure.waternets:
            for hl in waternet.HeadLines:
                for point in hl.Points:
                    point.X = ds.right - (point.X - ds.left)

        for cs in ds.model.datastructure.calculationsettings:
            if cs.Bishop is not None:
                cs.Bishop.Circle.Center.X = ds.right - (
                    cs.Bishop.Circle.Center.X - ds.left
                )
            if cs.BishopBruteForce is not None:
                cs.BishopBruteForce.SearchGrid.BottomLeft.X = ds.right - (
                    cs.BishopBruteForce.SearchGrid.BottomLeft.X - ds.left
                )
                cs.BishopBruteForce.SlipPlaneConstraints.XLeftZoneA = ds.right - (
                    cs.BishopBruteForce.SlipPlaneConstraints.XLeftZoneA - ds.left
                )
                cs.BishopBruteForce.SlipPlaneConstraints.XLeftZoneB = ds.right - (
                    cs.BishopBruteForce.SlipPlaneConstraints.XLeftZoneB - ds.left
                )
            if cs.Spencer.SlipPlane is not None:
                for point in cs.Spencer.SlipPlane:
                    point.X = ds.right - (point.X - ds.left)
            if cs.SpencerGenetic is not None:
                if cs.SpencerGenetic.SlipPlaneA is not None:
                    for point in cs.SpencerGenetic.SlipPlaneA:
                        point.X = ds.right - (point.X - ds.left)
                if cs.SpencerGenetic.SlipPlaneB is not None:
                    for point in cs.SpencerGenetic.SlipPlaneB:
                        point.X = ds.right - (point.X - ds.left)
            if cs.UpliftVan is not None:
                cs.UpliftVan.SlipPlane.FirstCircleCenter.X = ds.right - (
                    cs.UpliftVan.SlipPlane.FirstCircleCenter.X - ds.left
                )
                cs.UpliftVan.SlipPlane.SecondCircleCenter.X = ds.right - (
                    cs.UpliftVan.SlipPlane.SecondCircleCenter.X - ds.left
                )
            if cs.UpliftVanParticleSwarm is not None:
                if cs.UpliftVanParticleSwarm.SearchAreaA.TopLeft is not None:
                    cs.UpliftVanParticleSwarm.SearchAreaA.TopLeft.X = ds.right - (
                        cs.UpliftVanParticleSwarm.SearchAreaA.TopLeft.X - ds.left
                    )
                if cs.UpliftVanParticleSwarm.SearchAreaB.TopLeft is not None:
                    cs.UpliftVanParticleSwarm.SearchAreaB.TopLeft.X = ds.right - (
                        cs.UpliftVanParticleSwarm.SearchAreaB.TopLeft.X - ds.left
                    )
                cs.UpliftVanParticleSwarm.SlipPlaneConstraints.XLeftZoneA = ds.right - (
                    cs.UpliftVanParticleSwarm.SlipPlaneConstraints.XLeftZoneA - ds.left
                )
                cs.UpliftVanParticleSwarm.SlipPlaneConstraints.XLeftZoneB = ds.right - (
                    cs.UpliftVanParticleSwarm.SlipPlaneConstraints.XLeftZoneB - ds.left
                )

        for reinforcement in ds.model.datastructure.reinforcements:
            for nail in reinforcement.Nails:
                nail.Location.X = ds.right - (nail.Location.X - ds.left)
            for geotextile in reinforcement.Geotextiles:
                geotextile.Start.X = ds.right - (geotextile.Start.X - ds.left)
                geotextile.End.X = ds.right - (geotextile.End.X - ds.left)
            for fl in reinforcement.ForbiddenLines:
                fl.Start.X = ds.right - (fl.Start.X - ds.left)
                fl.End.X = ds.right - (fl.End.X - ds.left)

        for state in ds.model.datastructure.states:
            for sl in state.StateLines:
                for point in sl.Points:
                    point.X = ds.right - (point.X - ds.left)
            for point in state.StatePoints:
                point.Point.X = ds.right - (point.Point.X - ds.left)

        for cp in ds.characteristic_points:
            cp.x = ds.right - (cp.x - ds.left)

        ds._post_process()

        return ds
