# Wormy (a Nibbles clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

import random, pygame, sys
from pygame.locals import *

FPS = 50
WINDOWWIDTH = 1280
WINDOWHEIGHT = 960
CELLSIZE = 20
assert WINDOWWIDTH % CELLSIZE == 0, "Window width must be a multiple of cell size."
assert WINDOWHEIGHT % CELLSIZE == 0, "Window height must be a multiple of cell size."
CELLWIDTH = int(WINDOWWIDTH / CELLSIZE)
CELLHEIGHT = int(WINDOWHEIGHT / CELLSIZE)

#             R    G    B
WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
RED       = (255,   0,   0)
GREEN     = (  0, 255,   0)
DARKGREEN = (  0, 155,   0)
DARKGRAY  = ( 40,  40,  40)
PURPLE    = (255,   0, 255)
YELLOW    = (255, 255,   0)
BLUE      = (  0,   0, 255)
TURQUOISE = (127, 127, 255)
GRAY      = (100, 100, 100)
BGCOLOR = BLACK

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

HEAD = 0 # syntactic sugar: index of the worm's head

CENTRALIZED = False
NUM_WORMS_INIT = 2 # number of initial worms
LEN_LIMIT = 4
SECTOR_LIMIT = 4
APPLE_LIFETIME = 200
APPLE_SPAWN_FREQ = 50
NEIGHBORHOOD = 5

LASER_FREQ = 0.07
LASER_FULL_CHARGE = 30



def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT

    #random.seed(0)

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    pygame.time.set_timer(12, 30000)
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    pygame.display.set_caption('Medusa')

    showStartScreen()
    while True:
        runGame()
        showGameOverScreen()


def runGame():
    worms = []
    laserBeam = []
    stones = []
    for _ in range(NUM_WORMS_INIT):
        # Set a random start point.
        startx = random.randint(5, CELLWIDTH - 6)
        starty = random.randint(5, CELLHEIGHT - 6)
        worms.append({'coords': [
            {'x': startx,     'y': starty},
            {'x': startx - 1, 'y': starty},
            {'x': startx - 2, 'y': starty}
            ],
            'dir': RIGHT,
            'haveLaser': 0,
            'fireLaser': False,
            'gotApple': False,
            'sector': []})
    worms[0]['sector'] = [True]
    worms[1]['sector'] = [False]

    # Start the apples in random places.
    apples = []
    appleSpawnCount = 0
    laserPickup = False
    score = 0

    while True: # main game loop
        getActions(worms, apples)
        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT:
                terminate()



            elif event.type == KEYDOWN:
                # Controls all worms
                for worm in worms:
                    if (event.key == K_KP4) and worm['dir'] != RIGHT:
                        worm['dir'] = LEFT
                    elif (event.key == K_KP6) and worm['dir'] != LEFT:
                        worm['dir'] = RIGHT
                    elif (event.key == K_KP8) and worm['dir'] != DOWN:
                        worm['dir'] = UP
                    elif (event.key == K_KP2) and worm['dir'] != UP:
                        worm['dir'] = DOWN
                    elif (event.key == K_KP5):
                        worm['fireLaser'] = True

        # Split worms if too long
        for w in range(len(worms)):
            if len(worms[w]['coords']) == LEN_LIMIT:
                coords = []
                halfLen = LEN_LIMIT // 2
                while len(worms[w]['coords']) > halfLen:
                    coords.append(worms[w]['coords'][halfLen])
                    del worms[w]['coords'][halfLen]

                newWormy = {
                    'coords': coords, 
                    'dir': str(worms[w]['dir']),
                    'haveLaser': 0,
                    'fireLaser': False,
                    'gotApple': False,
                    'sector': list(worms[w]['sector'])
                    }
                if len(worms[w]['sector']) < SECTOR_LIMIT:
                    worms[w]['sector'].append(True)
                    newWormy['sector'].append(False)
                worms.append(newWormy)



        hit_gameover = -1
        wormToKill = []
        for w in range(len(worms)):
            # check if the worm has hit itself, the edge, or a stone
            if not isWithinGrid(worms[w]['coords'][HEAD]) or worms[w]['coords'][HEAD] in stones:
                hit_gameover = w # game over
            for wormBody in worms[w]['coords'][1:]:
                if wormBody['x'] == worms[w]['coords'][HEAD]['x'] and wormBody['y'] == worms[w]['coords'][HEAD]['y']:
                    hit_gameover = w # game over
            # or another worm, Longer worm dies
            for wother in range(len(worms)):
                if wother == w:
                    continue
                for indivWormCoords in worms[wother]['coords']:
                    if worms[w]['coords'][HEAD]['x'] == indivWormCoords['x'] and worms[w]['coords'][HEAD]['y'] == indivWormCoords['y']:
                        if len(worms[w]['coords']) < len(worms[wother]['coords']):
                            wormToKill.append(wother)
                        elif len(worms[w]['coords']) > len(worms[wother]['coords']):
                            wormToKill.append(w)
                        else:
                            #Delete newer worm
                            lr = min(w, wother)
                            wormToKill.append(lr)

        wormToKill = list(set(wormToKill)) #only unique worms
        wormToKill.sort(reverse=True)
        for w in wormToKill:
            del worms[w]

        for w in range(len(worms)):
            # handle laser collisions
            caught = False
            for c in range(len(worms[w]['coords'])):
                if worms[w]['coords'][c] in laserBeam:
                    caught = True
                if caught:
                    while c < len(worms[w]['coords']):
                        if worms[w]['coords'][c] not in laserBeam:
                            stones.append(dict(worms[w]['coords'][c]))
                        del worms[w]['coords'][c]
                    break
            if len(worms[w]['coords']) < 1:
                hit_gameover = w
                

            if hit_gameover != -1:
                break


            # check if worm has picked up laser
            if laserPickup != False and worms[w]['coords'][HEAD]['x'] == laserPickup['x'] and worms[w]['coords'][HEAD]['y'] == laserPickup['y']:
                del laserPickup
                laserPickup = False
                worms[w]['haveLaser'] = LASER_FULL_CHARGE

            eat = [apple for apple in apples if worms[w]['coords'][HEAD]['x'] == apple['x'] and worms[w]['coords'][HEAD]['y'] == apple['y']]
            # check if worm has eaten an apple
            if len(eat) > 0:
                worms[w]['gotApple'] = True
            else:
                worms[w]['gotApple'] = False

            for e in eat:
                score += 1
                apples.remove(e)
            
            # add new apples
            appleSpawnCount += 1
            if appleSpawnCount == APPLE_SPAWN_FREQ:
                appleSpawnCount = 0
                loc = getRandomLocation()
                while loc in stones:
                    loc = getRandomLocation()
                loc["time"] = getAppleLifetime()
                apples.append(loc) # set a new apple somewhere

            for a in range(len(apples)):
                if apples[a]['time'] > 0:
                    apples[a]['time'] -= 1

            newApples = []
            for apple in apples:
                if apple['time'] != 0:
                    newApples.append(apple)
                else:
                    score -= 1
            apples = [apple for apple in apples if apple['time'] != 0]

        # discard old laser beam coordinates
        laserBeam = []
        for w in range(len(worms)):
            if hit_gameover != -1:
                break
            # move the worm by adding a segment in the direction it is moving
            if worms[w]['dir'] == UP:
                newHead = {'x': worms[w]['coords'][HEAD]['x'], 'y': worms[w]['coords'][HEAD]['y'] - 1}
            elif worms[w]['dir'] == DOWN:
                newHead = {'x': worms[w]['coords'][HEAD]['x'], 'y': worms[w]['coords'][HEAD]['y'] + 1}
            elif worms[w]['dir'] == LEFT:
                newHead = {'x': worms[w]['coords'][HEAD]['x'] - 1, 'y': worms[w]['coords'][HEAD]['y']}
            elif worms[w]['dir'] == RIGHT:
                newHead = {'x': worms[w]['coords'][HEAD]['x'] + 1, 'y': worms[w]['coords'][HEAD]['y']}
            worms[w]['coords'].insert(HEAD, newHead)

            if worms[w]['gotApple'] == False:
                del worms[w]['coords'][-1] # remove worm's tail segment

            # make laser beam
            if worms[w]['fireLaser'] and worms[w]['haveLaser'] > 0:
                worms[w]['fireLaser'] = False
                worms[w]['haveLaser'] = 0
                laserCoord = dict(worms[w]['coords'][HEAD])
                while isWithinGrid(laserCoord):
                    if worms[w]['dir'] == UP:
                        laserCoord['y'] -= 1
                    elif worms[w]['dir'] == DOWN:
                        laserCoord['y'] += 1
                    elif worms[w]['dir'] == LEFT:
                        laserCoord['x'] -= 1
                    elif worms[w]['dir'] == RIGHT:
                        laserCoord['x'] += 1
                    
                    laserBeam.append(dict(laserCoord))


        DISPLAYSURF.fill(BGCOLOR)
        drawGrid()
        for worm in worms:
            drawWorm(worm['coords'], worm['haveLaser'])
            if worm['haveLaser'] > 0:
                worm['haveLaser'] -= 1

        drawApples(apples)

        if laserPickup == False: # Get location once
            if LASER_FREQ > random.random(): # with probability
                laserPickup = getRandomLocation()
                while laserPickup in stones:
                    laserPickup = getRandomLocation()
                
        if laserPickup != False: # Draw every time it exists
            drawLaserPickup(laserPickup)

        drawStones(stones)

        drawLaserBeam(laserBeam)

        drawScore(score)

        #TODO stuffs
        pygame.display.update()
        FPSCLOCK.tick(FPS)
        # End game if a worm hit something
        if hit_gameover != -1:
            return

def drawPressKeyMsg():
    pressKeySurf = BASICFONT.render('Press a key to play.', True, DARKGRAY)
    pressKeyRect = pressKeySurf.get_rect()
    pressKeyRect.topleft = (WINDOWWIDTH - 200, WINDOWHEIGHT - 30)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)


def checkForKeyPress():
    if len(pygame.event.get(QUIT)) > 0:
        terminate()

    keyUpEvents = pygame.event.get(KEYUP)
    if len(keyUpEvents) == 0:
        return None
    if keyUpEvents[0].key == K_ESCAPE:
        terminate()
    return keyUpEvents[0].key


def showStartScreen():
    titleFont = pygame.font.Font('freesansbold.ttf', 100)
    titleSurf1 = titleFont.render('Medusa!', True, PURPLE, YELLOW)
    titleSurf2 = titleFont.render('Medusa!', True, BLUE)

    degrees1 = 0
    degrees2 = 0
    while True:
        DISPLAYSURF.fill(BGCOLOR)
        rotatedSurf1 = pygame.transform.rotate(titleSurf1, degrees1)
        rotatedRect1 = rotatedSurf1.get_rect()
        rotatedRect1.center = (WINDOWWIDTH / 2, WINDOWHEIGHT / 2)
        DISPLAYSURF.blit(rotatedSurf1, rotatedRect1)

        rotatedSurf2 = pygame.transform.rotate(titleSurf2, degrees2)
        rotatedRect2 = rotatedSurf2.get_rect()
        rotatedRect2.center = (WINDOWWIDTH / 2, WINDOWHEIGHT / 2)
        DISPLAYSURF.blit(rotatedSurf2, rotatedRect2)

        drawPressKeyMsg()

        if checkForKeyPress():
            pygame.event.get() # clear event queue
            return
        pygame.display.update()
        FPSCLOCK.tick(FPS)
        degrees1 += 3 # rotate by 3 degrees each frame
        degrees2 += 7 # rotate by 7 degrees each frame


def terminate():
    pygame.quit()
    sys.exit()


def getRandomLocation():
    return {'x': random.randint(0, CELLWIDTH - 1), 'y': random.randint(0, CELLHEIGHT - 1)}



def showGameOverScreen():
    gameOverFont = pygame.font.Font('freesansbold.ttf', 150)
    gameSurf = gameOverFont.render('Game', True, WHITE)
    overSurf = gameOverFont.render('Over', True, WHITE)
    gameRect = gameSurf.get_rect()
    overRect = overSurf.get_rect()
    gameRect.midtop = (WINDOWWIDTH / 2, 10)
    overRect.midtop = (WINDOWWIDTH / 2, gameRect.height + 10 + 25)

    DISPLAYSURF.blit(gameSurf, gameRect)
    DISPLAYSURF.blit(overSurf, overRect)
    drawPressKeyMsg()
    pygame.display.update()
    pygame.time.wait(500)
    checkForKeyPress() # clear out any key presses in the event queue

    while True:
        if checkForKeyPress():
            pygame.event.get() # clear event queue
            return

def drawScore(score):
    scoreStr = 'Score: ' + str(score)
    scoreSurf = BASICFONT.render(scoreStr, True, WHITE)
    scoreRect = scoreSurf.get_rect()
    scoreRect.topleft = (10, 10)
    DISPLAYSURF.blit(scoreSurf, scoreRect)


def drawWorm(wormCoords, hasLaser):
    for coord in wormCoords:
        x = coord['x'] * CELLSIZE
        y = coord['y'] * CELLSIZE
        wormSegmentRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)

        colors = (DARKGREEN, GREEN)
        if hasLaser > 0:
            colors = (BLUE, TURQUOISE)

        pygame.draw.rect(DISPLAYSURF, colors[0], wormSegmentRect)
        wormInnerSegmentRect = pygame.Rect(x + 4, y + 4, CELLSIZE - 8, CELLSIZE - 8)
        pygame.draw.rect(DISPLAYSURF, colors[1], wormInnerSegmentRect)
        


def drawApples(coords):
    for coord in coords:
        x = coord['x'] * CELLSIZE
        y = coord['y'] * CELLSIZE
        appleRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
        pygame.draw.rect(DISPLAYSURF, RED, appleRect)


def drawGrid():
    for x in range(0, WINDOWWIDTH, CELLSIZE): # draw vertical lines
        pygame.draw.line(DISPLAYSURF, DARKGRAY, (x, 0), (x, WINDOWHEIGHT))
    for y in range(0, WINDOWHEIGHT, CELLSIZE): # draw horizontal lines
        pygame.draw.line(DISPLAYSURF, DARKGRAY, (0, y), (WINDOWWIDTH, y))

def drawLaserBeam(coords):
    for coord in coords:
        x = coord['x'] * CELLSIZE
        y = coord['y'] * CELLSIZE
        laserRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
        pygame.draw.rect(DISPLAYSURF, YELLOW, laserRect)


def drawLaserPickup(coord):
    x = coord['x'] * CELLSIZE
    y = coord['y'] * CELLSIZE
    laserRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
    pygame.draw.rect(DISPLAYSURF, TURQUOISE, laserRect)

def drawStones(coords):
    for coord in coords:
        x = coord['x'] * CELLSIZE
        y = coord['y'] * CELLSIZE
        stoneSegmentRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
        pygame.draw.rect(DISPLAYSURF, DARKGRAY, stoneSegmentRect)
        stoneSegmentRect = pygame.Rect(x + 4, y + 4, CELLSIZE - 8, CELLSIZE - 8)
        pygame.draw.rect(DISPLAYSURF, GRAY, stoneSegmentRect)

def getActions(worms, apples):
    # Move with some randomness
    # Go toward apples if within sensing radius
    # Don't hit walls
    prob_dirchange = 0.4
    # Randomness
    for worm in worms:
        change = random.randint(0,1)
        changeDir = random.uniform(0,1) < prob_dirchange
        sa = senseApple(worm['coords'][HEAD], apples)
        # beyond corners
        bounds = getBoundaries(worm)

        if worm['coords'][HEAD]['x'] <= bounds['xmin'] and worm['coords'][HEAD]['y'] <= bounds['ymin']:
            if worm['dir'] == UP:
                worm['dir'] = RIGHT
            elif worm['dir'] == LEFT:
                worm['dir'] = DOWN

        elif worm['coords'][HEAD]['x'] <= bounds['xmin'] and worm['coords'][HEAD]['y'] >= bounds['ymax']:
            if worm['dir'] == DOWN:
                worm['dir'] = RIGHT
            elif worm['dir'] == LEFT:
                worm['dir'] = UP

        elif worm['coords'][HEAD]['x'] >= bounds['xmax'] and worm['coords'][HEAD]['y'] <= bounds['ymin']:
            if worm['dir'] == UP:
                worm['dir'] = LEFT
            elif worm['dir'] == RIGHT:
                worm['dir'] = DOWN

        elif worm['coords'][HEAD]['x'] >= bounds['xmax'] and worm['coords'][HEAD]['y'] >= bounds['ymax']:
            if worm['dir'] == DOWN:
                worm['dir'] = LEFT
            elif worm['dir'] == RIGHT:
                worm['dir'] = UP

        # out of bounds
        elif worm['coords'][HEAD]['x'] < bounds['xmin']:
            if worm['dir'] == LEFT:
                if change == 0:
                    worm['dir'] = UP
                elif change == 1:
                    worm['dir'] = DOWN
            elif worm['dir'] == UP or worm['dir'] == DOWN:
                worm['dir'] = RIGHT

        elif worm['coords'][HEAD]['x'] > bounds['xmax']:
            if worm['dir'] == RIGHT:
                if change == 0:
                    worm['dir'] = UP
                elif change == 1:
                    worm['dir'] = DOWN
            elif worm['dir'] == UP or worm['dir'] == DOWN:
                worm['dir'] = LEFT

        elif worm['coords'][HEAD]['y'] < bounds['ymin']:
            if worm['dir'] == UP:
                if change == 0:
                    worm['dir'] = LEFT
                elif change == 1:
                    worm['dir'] = RIGHT
            elif worm['dir'] == LEFT or worm['dir'] == RIGHT:
                worm['dir'] = DOWN

        elif worm['coords'][HEAD]['y'] > bounds['ymax']:
            if worm['dir'] == DOWN:
                if change == 0:
                    worm['dir'] = LEFT
                elif change == 1:
                    worm['dir'] = RIGHT
            elif worm['dir'] == LEFT or worm['dir'] == RIGHT:
                worm['dir'] = UP

        # on bounds
        elif worm['coords'][HEAD]['x'] == bounds['xmin']:
            if worm['dir'] == LEFT:
                if change == 0:
                    worm['dir'] = UP
                elif change == 1:
                    worm['dir'] = DOWN
            elif worm['dir'] == UP or worm['dir'] == DOWN:
                if changeDir and change == 1:
                    worm['dir'] = RIGHT

        elif worm['coords'][HEAD]['x'] == bounds['xmax']:
            if worm['dir'] == RIGHT:
                if change == 0:
                    worm['dir'] = UP
                elif change == 1:
                    worm['dir'] = DOWN
            elif worm['dir'] == UP or worm['dir'] == DOWN:
                if changeDir and change == 0:
                    worm['dir'] = LEFT

        elif worm['coords'][HEAD]['y'] == bounds['ymin']:
            if worm['dir'] == UP:
                if change == 0:
                    worm['dir'] = LEFT
                elif change == 1:
                    worm['dir'] = RIGHT
            elif worm['dir'] == LEFT or worm['dir'] == RIGHT:
                if changeDir and change == 1:
                    worm['dir'] = DOWN

        elif worm['coords'][HEAD]['y'] == bounds['ymax']:
            if worm['dir'] == DOWN:
                if change == 0:
                    worm['dir'] = LEFT
                elif change == 1:
                    worm['dir'] = RIGHT
            elif worm['dir'] == LEFT or worm['dir'] == RIGHT:
                if changeDir and change == 0:
                    worm['dir'] = UP

        elif sa != {}:
            if sa['x'] < 0 and sa['y'] <= 0 and worm['dir'] != RIGHT:
                worm['dir'] = LEFT
            elif sa['x'] >= 0 and sa['y'] < 0 and worm['dir'] != DOWN:
                worm['dir'] = UP
            elif sa['x'] > 0 and sa['y'] >= 0 and worm['dir'] != LEFT:
                worm['dir'] = RIGHT
            elif sa['x'] <= 0 and sa['y'] > 0 and worm['dir'] != UP:
                worm['dir'] = DOWN

        elif changeDir:
            if worm['dir'] == UP or worm['dir'] == DOWN:
                if change == 0:
                    worm['dir'] = LEFT
                elif change == 1:
                    worm['dir'] = RIGHT
            elif worm['dir'] == LEFT or worm['dir'] == RIGHT:
                if change == 0:
                    worm['dir'] = UP
                elif change == 1:
                    worm['dir'] = DOWN

def senseApple(wormHead, apples):
    dist = {}
    for apple in apples:
        xDiff = apple['x'] - wormHead['x']
        yDiff = apple['y'] - wormHead['y']
        if abs(xDiff) <= NEIGHBORHOOD and abs(yDiff) <= NEIGHBORHOOD:
            dist['x'] = xDiff
            dist['y'] = yDiff
            break # just first apple seen
    return dist

def getAppleLifetime():
    if type(APPLE_LIFETIME) is int:
        return APPLE_LIFETIME
    elif type(APPLE_LIFETIME) is tuple:
        return random.randint(APPLE_LIFETIME[0], APPLE_LIFETIME[1])

def getBoundaries(worm):
    bounds = {}
    bounds['xmin'] = 0
    bounds['xmax'] = CELLWIDTH - 1
    bounds['ymin'] = 0
    bounds['ymax'] = CELLHEIGHT - 1
    if CENTRALIZED:
        maxIters = SECTOR_LIMIT
        even = False
        for s in worm['sector']:
            if maxIters == 0:
                break
            maxIters -= 1
            even = not even

            if even:
                if s:
                    bounds['xmax'] = (bounds['xmin'] + bounds['xmax']) // 2
                else:
                    bounds['xmin'] = (bounds['xmin'] + bounds['xmax']) // 2 + 1
            else:
                if s: 
                    bounds['ymax'] = (bounds['ymin'] + bounds['ymax']) // 2
                else:
                    bounds['ymin'] = (bounds['ymin'] + bounds['ymax']) // 2 + 1

        
    return bounds


def isWithinGrid(coord):
    return coord['x'] > -1 and coord['x'] < CELLWIDTH and coord['y'] > -1 and coord['y'] < CELLHEIGHT


def maybeSpawnLaser(coord):
    if LASER_FREQ > random.random():
        return
    x = coord['x'] * CELLSIZE
    y = coord['y'] * CELLSIZE
    laserRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
    pygame.draw.rect(DISPLAYSURF, TURQUOISE, laserRect)


if __name__ == '__main__':
    main()