# Agile Energy Planner

## Octopus Agile - Energy Use Planner

### Summary

This is a project to take advantage of the best times to use electricity
on the Octopus Agile tariff. In the transition to green energy, intermittency of renewable
energy supplies present a serious problem. In building this I hope to do my tiny part to balance the
grid and facilitate the transition. (I tell myself I might save some money on my bills, I won't,
and even if I did - it would hardly be worth the hassle!)

The project is nascent and intended for my personal use, but I am putting it online in case anyone
wants to make use of it, or join in on the development. It comes with no warranty, or guarantee of any updates!

My plan is to put this on a Raspberry Pi with a relay shield to control the hot-water
cylinder and heating at home too.


### Features

* Start & Stop Tesla Charging (via API)
* Tell users when good times to use appliances (via Email (SMS coming soon))
* Show historical price data and usage


### Planned Features

* Heat hot-water when electricity is cheaper than gas.


### Install

Detailed install instructions are not available. Reach out if you want to run it and I'll write some.

In summary though:

* Requires Python 3.9 (to merge dictionaries `{}|{}`)
  * `sudo apt install python3.9 python3.9-dev`
* Install the requirements (in your venv)
  * `pip install -r requirements.txt`
* Install Redis Server (for celery)
  * `sudo apt install redis`
* Note I developed on a Mac, and have started to put on an Rpi, but probably will need mods before running properly. 

