"""The rotated room uses the same journey logic and correctly rotated belt load points."""
def initialize(game):
 game.event('Rotated check-in28 ready',degrees=-90,architecture_unchanged=True)
 if '-Checkin28QA' in game.CMD:
  import checkin28_qa;checkin28_qa.start(game)
