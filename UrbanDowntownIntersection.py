import py_trees
import carla
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import *
from srunner.scenariomanager.scenarioatomics.atomic_criteria import *
from srunner.scenarios.basic_scenario import BasicScenario


class UrbanConstructionEmergency(BasicScenario):
    
    # Entry class for `UrbanConstructionEmergency`.
    

    category = "UrbanConstructionEmergency"
    timeout = 120          # seconds
    town = "Town03"

    def __init__(self, world, ego_vehicles, config,
                 randomize=False, debug_mode=False):
        super().__init__(
            "UrbanConstructionEmergency",
            ego_vehicles,
            config,
            world,
            debug_mode=debug_mode,
            terminate_on_failure=False,
            criteria_enable=True
        )

    # ------------------------------------------------------------------ #
    def _initialize_actors(self, config):
        #Spawn all non-ego actors.

        world = CarlaDataProvider.get_world()
        bp_lib = world.get_blueprint_library()

        # ---------- Weather ----------
        weather = carla.WeatherParameters(
            cloudiness=50.0,
            precipitation=20.0,
            sun_altitude_angle=45.0
        )
        world.set_weather(weather)

        # ---------- Construction zone ----------
        cone_bp = bp_lib.find("static.prop.trafficcone")
        base_tf = config.other_actors[0].transform  # from XML
        cones = []
        for i in range(5):
            offset = carla.Location(x=i*2.0, y=0, z=0)
            cone_tf = carla.Transform(
                carla.Location(base_tf.location + offset),
                base_tf.rotation
            )
            cone = world.try_spawn_actor(cone_bp, cone_tf)
            if cone:
                self.other_actors.append(cone)

        # ---------- Emergency vehicle ----------
        amb_bp = bp_lib.find("vehicle.ford.ambulance")
        amb_tf = config.other_actors[1].transform
        ambulance = world.try_spawn_actor(amb_bp, amb_tf)
        if ambulance:
            ambulance.set_autopilot(True, CarlaDataProvider.get_traffic_manager_port())
            self.other_actors.append(ambulance)

        # ---------- NPC vehicles ----------
        spawn_points = world.get_map().get_spawn_points()
        npc_bps = [b for b in bp_lib.filter("vehicle.*") if "bicycle" not in b.id and "yamaha" not in b.id]
        for i in range(5):
            tf_npc = spawn_points[(i+10) % len(spawn_points)]
            npc = world.try_spawn_actor(random.choice(npc_bps), tf_npc)
            if npc:
                npc.set_autopilot(True, CarlaDataProvider.get_traffic_manager_port())
                self.other_actors.append(npc)

        # ---------- Cyclist (Yamaha YZF) ----------
        cyc_bp = bp_lib.find("vehicle.yamaha.yzf")
        cyc_tf = spawn_points[20 % len(spawn_points)]
        cyclist = world.try_spawn_actor(cyc_bp, cyc_tf)
        if cyclist:
            cyclist.set_autopilot(True, CarlaDataProvider.get_traffic_manager_port())
            self.other_actors.append(cyclist)

        # ---------- Pedestrians ----------
        walker_bps = bp_lib.filter("walker.pedestrian.*")
        for i in range(10):
            loc = world.get_random_location_from_navigation()
            if loc:
                walker_bp = random.choice(walker_bps)
                spawn_tf = carla.Transform(loc)
                walker = world.try_spawn_actor(walker_bp, spawn_tf)
                if walker:
                    ctrl_bp = bp_lib.find("controller.ai.walker")
                    ctrl = world.spawn_actor(ctrl_bp, carla.Transform(), attach_to=walker)
                    ctrl.start()
                    ctrl.go_to_location(world.get_random_location_from_navigation())
                    ctrl.set_max_speed(1.2 + random.random())
                    self.other_actors.extend([walker, ctrl])

    # ------------------------------------------------------------------ #
    def _create_behavior(self):
        # Keep scenario alive for <timeout> seconds
        root = py_trees.composites.Sequence("Root")
        root.add_child(Idle(timeout=self.timeout))
        return root

    # ------------------------------------------------------------------ #
    def _create_test_criteria(self):
        criteria = []
        for ego in self.ego_vehicles:
            criteria.append(CollisionTest(ego))
            criteria.append(RunningStopTest(ego))
        return criteria
    
    
    # Scenario-Runner scenario:
# Urban Downtown Intersection (Town03)
# - Light rain, overcast midday
# - Construction zone (traffic-cone lane closure)
# - Emergency vehicle (Ford Ambulance)
# - NPC vehicles, pedestrians, cyclist
