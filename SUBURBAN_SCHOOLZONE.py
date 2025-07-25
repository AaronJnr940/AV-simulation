import py_trees
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import *
from srunner.scenariomanager.scenarioatomics.atomic_criteria import *
from srunner.scenariomanager.timer import GameTime
from srunner.scenarios.basic_scenario import BasicScenario

class SuburbanSchoolZone(BasicScenario):
    
    # A suburban residential street that includes
    #   - parked cars
    #   - a ‘school-bus’ (Nissan Patrol)
    #   - pedestrians (children)
    #   - early-morning weather (low sun + light fog)
    

    category = "SuburbanSchoolZone"
    timeout    = 120        # seconds
    town       = "Town03"   # or any map with residential roads

    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False):
        self._map = world.get_map()
        self._ego_route = None        # no fixed route, open driving

        # ---------- actor parameters ----------
        self._num_parked   = 5
        self._num_dynamic  = 3
        self._num_children = 5
        self._bus_model    = "vehicle.nissan.patrol"
        self._ego_model    = "vehicle.toyota.prius"

        super().__init__(
            name           = "SuburbanSchoolZone",
            ego_vehicles   = ego_vehicles,
            config         = config,
            world          = world,
            debug_mode     = debug_mode,
            terminate_on_failure=False,
            criteria_enable  = True
        )

    # ------------------------------------------------------------------ #
    def _initialize_actors(self, config):
        # Spawn everything that is NOT the ego-vehicle.
        world = CarlaDataProvider.get_world()
        bp_lib = world.get_blueprint_library()

        # 1. Static (parked) vehicles
        for i in range(self._num_parked):
            bp = bp_lib.filter("vehicle.*")[i % len(bp_lib.filter("vehicle.*"))]
            spawn_tf = CarlaDataProvider.get_world().get_map().get_spawn_points()[i+1]
            parked = world.try_spawn_actor(bp, spawn_tf)
            if parked:
                parked.set_simulate_physics(False)
                parked.set_velocity(carla.Vector3D(0,0,0))
                self.other_actors.append(parked)

        # 2. Dynamic vehicles (entering/exiting driveways)
        for i in range(self._num_dynamic):
            bp = bp_lib.filter("vehicle.*")[i+10]
            spawn_tf = CarlaDataProvider.get_world().get_map().get_spawn_points()[i+10]
            dyn = world.try_spawn_actor(bp, spawn_tf)
            if dyn:
                self.other_actors.append(dyn)
                dyn.set_autopilot(True, CarlaDataProvider.get_traffic_manager_port())

        # 3. School-bus substitute
        bus_bp = bp_lib.find(self._bus_model)
        tf = CarlaDataProvider.get_world().get_map().get_spawn_points()[20]
        bus = world.try_spawn_actor(bus_bp, tf)
        if bus:
            self.other_actors.append(bus)
            bus.set_autopilot(True, CarlaDataProvider.get_traffic_manager_port())

        # 4. Pedestrians (children)
        walker_bp = bp_lib.filter("walker.pedestrian.*")
        for i in range(self._num_children):
            bp = walker_bp[i % len(walker_bp)]
            spawn_tf = CarlaDataProvider.get_world().get_map().get_spawn_points()[i+30]
            wp = world.get_map().get_waypoint(spawn_tf.location)
            spawn_tf.location.z = wp.transform.location.z + 1.0
            child = world.try_spawn_actor(bp, spawn_tf)
            if child:
                self.other_actors.append(child)
                controller_bp = bp_lib.find("controller.ai.walker")
                ctrl = world.spawn_actor(controller_bp, carla.Transform(), attach_to=child)
                ctrl.start()
                ctrl.go_to_location(world.get_random_location_from_navigation())
                ctrl.set_max_speed(1.2)
                self.other_actors.append(ctrl)

        # 5. Early-morning weather
        weather = carla.WeatherParameters(
            cloudiness=20,
            sun_altitude_angle=15,
            fog_density=20,
            wetness=30
        )
        world.set_weather(weather)

    # ------------------------------------------------------------------ #
    def _create_behavior(self):
      
        # Minimal behaviour: keep scenario alive for 'timeout' seconds.
       
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