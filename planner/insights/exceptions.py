
class NoSolutions(Exception):
    """Exception for failure to find a solution given requested inputs."""
    pass


class NoCrystalBall(Exception):
    """Data isn't available  for the time-horizon you are looking for"""
    pass
