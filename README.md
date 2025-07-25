Automated Generation of Test Scenarios for Autonomous Driving using LLMs

The experiments were conducted by prompting a pre-trained Llama 3 model to generate scripts and execute said scripts using ScenarioRunner via its Python API. Simulations were initialized alternating between CARLA versions 0.9.13 and 0.9.15. Most importantly, to ensure CARLA is connected properly, a jupyter notebook file is created beforehand and this serves as a means of firstly establishing connection to the client via its python API and checking for assets such as available maps, vehicle blue-prints, available props etc. This is done because the different CARLA versions may or may not have some assets to properly execute the simulation. 

Keywords: large language models; generation, Operational Design Domain; autono-mous vehicles; simulation; CARLA; ScenarioRunner; prompt-engineering; fine-tuning 
