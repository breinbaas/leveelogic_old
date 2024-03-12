from copy import deepcopy

from ..dstability import DStability
from .algorithm import Algorithm
from ...helpers import polyline_polyline_intersections


class AlgorithmMove(Algorithm):
    dx: float

    def _check_input(self):
        pass

    def _execute(self) -> DStability:
        ds = deepcopy(self.ds)

        # gemoetries
        for geom in ds.model.datastructure.geometries:
            for layer in geom.Layers:
                for point in layer.Points:
                    point.X = float(point.X) + self.dx

        # loads
        for loads in ds.model.datastructure.loads:
            for load in loads.LineLoads:
                load.Location.X += self.dx
            for load in loads.UniformLoads:
                load.End += self.dx
                load.Start += self.dx
            for load in loads.Trees:
                load.Location.X += self.dx

        for decoration in ds.model.datastructure.decorations:
            for elevation in decoration.Elevations:
                for point in elevation.Points:
                    point.X = float(point.X) + self.dx
            for excavation in decoration.Excavations:
                for point in excavation.Points:
                    point.X = float(point.X) + self.dx

        for waternet in ds.model.datastructure.waternets:
            for hl in waternet.HeadLines:
                for point in hl.Points:
                    point.X = float(point.X) + self.dx
            for rl in waternet.ReferenceLines:
                for point in rl.Points:
                    point.X = float(point.X) + self.dx

        for cs in ds.model.datastructure.calculationsettings:
            if cs.Bishop is not None:
                cs.Bishop.Circle.Center.X = float(cs.Bishop.Circle.Center.X) + self.dx
            if cs.BishopBruteForce is not None:
                if cs.BishopBruteForce.SearchGrid.BottomLeft is not None:
                    cs.BishopBruteForce.SearchGrid.BottomLeft.X = (
                        float(cs.BishopBruteForce.SearchGrid.BottomLeft.X) + self.dx
                    )
                if cs.BishopBruteForce.SlipPlaneConstraints is not None:
                    cs.BishopBruteForce.SlipPlaneConstraints.XLeftZoneA = (
                        float(cs.BishopBruteForce.SlipPlaneConstraints.XLeftZoneA)
                        + self.dx
                    )
                    cs.BishopBruteForce.SlipPlaneConstraints.XLeftZoneB = (
                        float(cs.BishopBruteForce.SlipPlaneConstraints.XLeftZoneB)
                        + self.dx
                    )
            if cs.Spencer.SlipPlane is not None:
                for point in cs.Spencer.SlipPlane:
                    point.X = float(point.X) + self.dx
            if cs.SpencerGenetic is not None:
                if cs.SpencerGenetic.SlipPlaneA is not None:
                    for point in cs.SpencerGenetic.SlipPlaneA:
                        point.X = float(point.X) + self.dx
                if cs.SpencerGenetic.SlipPlaneB is not None:
                    for point in cs.SpencerGenetic.SlipPlaneB:
                        point.X = float(point.X) + self.dx
            if cs.UpliftVan is not None:
                cs.UpliftVan.SlipPlane.FirstCircleCenter.X = (
                    float(cs.UpliftVan.SlipPlane.FirstCircleCenter.X) + self.dx
                )
                cs.UpliftVan.SlipPlane.SecondCircleCenter.X = (
                    float(cs.UpliftVan.SlipPlane.SecondCircleCenter.X) + self.dx
                )
            if cs.UpliftVanParticleSwarm is not None:
                if cs.UpliftVanParticleSwarm.SearchAreaA.TopLeft is not None:
                    cs.UpliftVanParticleSwarm.SearchAreaA.TopLeft.X = (
                        float(cs.UpliftVanParticleSwarm.SearchAreaA.TopLeft.X) + self.dx
                    )
                if cs.UpliftVanParticleSwarm.SearchAreaB.TopLeft is not None:
                    cs.UpliftVanParticleSwarm.SearchAreaB.TopLeft.X = (
                        float(cs.UpliftVanParticleSwarm.SearchAreaB.TopLeft.X) + self.dx
                    )
                cs.UpliftVanParticleSwarm.SlipPlaneConstraints.XLeftZoneA = (
                    float(cs.UpliftVanParticleSwarm.SlipPlaneConstraints.XLeftZoneA)
                    + self.dx
                )
                cs.UpliftVanParticleSwarm.SlipPlaneConstraints.XLeftZoneB = (
                    float(cs.UpliftVanParticleSwarm.SlipPlaneConstraints.XLeftZoneB)
                    + self.dx
                )

        for reinforcement in ds.model.datastructure.reinforcements:
            for nail in reinforcement.Nails:
                nail.Location.X = float(nail.Location.X) + self.dx
            for geotextile in reinforcement.Geotextiles:
                geotextile.Start.X = float(geotextile.Start.X) + self.dx
                geotextile.End.X = float(geotextile.End.X) + self.dx
            for fl in reinforcement.ForbiddenLines:
                fl.Start.X = float(fl.Start.X) + self.dx
                fl.End.X = float(fl.End.X) + self.dx

        for state in ds.model.datastructure.states:
            for sl in state.StateLines:
                for point in sl.Points:
                    point.X = float(point.X) + self.dx
                for value in sl.Values:
                    value.X = float(value.X) + self.dx
            for point in state.StatePoints:
                point.Point.X = float(point.Point.X) + self.dx

        for cp in ds.characteristic_points:
            cp.x = float(cp.x) + self.dx

        ds._post_process()

        return ds
