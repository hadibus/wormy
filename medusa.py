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
APPLE_LIFETIME = (80, 100)
APPLE_SPAWN_FREQ = 15
NEIGHBORHOOD = 5

LASER_FREQ = 0.07
LASER_FULL_CHARGE = 30



def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT

    #random.seed(0)

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    pygame.display.set_caption('Medusa')

    showStartScreen()
    while True:
        runGame()
        showGameOverScreen()


def runGame():
    wormCoords = []
    direction = []
    haveLaser = []
    fireLaser = []
    laserBeam = []
    stones = []
    gotApples = []
    wormSectors = [[True],[False]]
    for _ in range(NUM_WORMS_INIT):
        haveLaser.append(0)
        fireLaser.append(False)
        gotApples.append(False)
        # Set a random start point.
        startx = random.randint(5, CELLWIDTH - 6)
        starty = random.randint(5, CELLHEIGHT - 6)
        wormCoords.append([
            {'x': startx,     'y': starty},
            {'x': startx - 1, 'y': starty},
            {'x': startx - 2, 'y': starty}
            ])
        direction.append(RIGHT)

    # Start the apples in random places.
    apples = []
    appleSpawnCount = 0
    laserPickup = False
    score = 0

    while True: # main game loop
        direction = getActions(wormCoords, direction, apples)
        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT:
                terminate()



            elif event.type == KEYDOWN:
                # Controls all worms
                for d in range(len(wormCoords)):
                    if (event.key == K_KP4) and direction[d] != RIGHT:
                        direction[d] = LEFT
                    elif (event.key == K_KP6) and direction[d] != LEFT:
                        direction[d] = RIGHT
                    elif (event.key == K_KP8) and direction[d] != DOWN:
                        direction[d] = UP
                    elif (event.key == K_KP2) and direction[d] != UP:
                        direction[d] = DOWN
                    elif (event.key == K_KP5):
                        fireLaser[d] = True

        # Split worms if too long
        for w in range(len(wormCoords)):
            if len(wormCoords[w]) == LEN_LIMIT:
                coords = []
                halfLen = LEN_LIMIT // 2
                while len(wormCoords[w]) > LEN_LIMIT / 2:
                    coords.append(wormCoords[w][halfLen])
                    del wormCoords[w][halfLen]
                wormCoords.append(coords)
                direction.append(direction[w])
                gotApples.append(False)
                fireLaser.append(False)
                haveLaser.append(False)


        hit_gameover = -1
        wormToKill = []
        for w in range(len(wormCoords)):
            # check if the worm has hit itself, the edge, or a stone
            if not isWithinGrid(wormCoords[w][HEAD]) or wormCoords[w][HEAD] in stones:
                hit_gameover = w # game over
            for wormBody in wormCoords[w][1:]:
                if wormBody['x'] == wormCoords[w][HEAD]['x'] and wormBody['y'] == wormCoords[w][HEAD]['y']:
                    hit_gameover = w # game over
            # or another worm, Longer worm dies
            for wother in range(len(wormCoords)):
                if wother == w:
                    continue
                for indivWormCoords in wormCoords[wother]:
                    if wormCoords[w][HEAD]['x'] == indivWormCoords['x'] and wormCoords[w][HEAD]['y'] == indivWormCoords['y']:
                        if len(wormCoords[w]) < len(wormCoords[wother]):
                            wormToKill.append(wother)
                        elif len(wormCoords[w]) > len(wormCoords[wother]):
                            wormToKill.append(w)
                        else:
                            #Delete older worm
                            lr = min(w, wother)
                            wormToKill.append(lr)

        wormToKill = list(set(wormToKill)) #only unique worms
        wormToKill.sort(reverse=True)
        for val in wormToKill:
            del wormCoords[val]
            del gotApples[val]
            del direction[val]
            del fireLaser[val]
            del haveLaser[val]

        for w in range(len(wormCoords)):
            # handle laser collisions
            caught = False
            for c in range(len(wormCoords[w])):
                if wormCoords[w][c] in laserBeam:
                    caught = True
                if caught:
                    while c < len(wormCoords[w]):
                        if wormCoords[w][c] not in laserBeam:
                            stones.append(dict(wormCoords[w][c]))
                        del wormCoords[w][c]
                    break
            if len(wormCoords[w]) < 1:
                hit_gameover = w
                

            if hit_gameover != -1:
                break


            # check if worm has picked up laser
            if laserPickup != False and wormCoords[w][HEAD]['x'] == laserPickup['x'] and wormCoords[w][HEAD]['y'] == laserPickup['y']:
                del laserPickup
                laserPickup = False
                haveLaser[w] = LASER_FULL_CHARGE

            eat = [apple for apple in apples if wormCoords[w][HEAD]['x'] == apple['x'] and wormCoords[w][HEAD]['y'] == apple['y']]
            # check if worm has eaten an apple
            if len(eat) > 0:
                gotApples[w] = True
            else:
                gotApples[w] = False

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
        for w in range(len(wormCoords)):
            if hit_gameover != -1:
                break
            # move the worm by adding a segment in the direction it is moving
            if direction[w] == UP:
                newHead = {'x': wormCoords[w][HEAD]['x'], 'y': wormCoords[w][HEAD]['y'] - 1}
            elif direction[w] == DOWN:
                newHead = {'x': wormCoords[w][HEAD]['x'], 'y': wormCoords[w][HEAD]['y'] + 1}
            elif direction[w] == LEFT:
                newHead = {'x': wormCoords[w][HEAD]['x'] - 1, 'y': wormCoords[w][HEAD]['y']}
            elif direction[w] == RIGHT:
                newHead = {'x': wormCoords[w][HEAD]['x'] + 1, 'y': wormCoords[w][HEAD]['y']}
            wormCoords[w].insert(HEAD, newHead)

            if gotApples[w] == False:
                del wormCoords[w][-1] # remove worm's tail segment

            # make laser beam
            if fireLaser[w] and haveLaser[w] > 0:
                fireLaser[w] = False
                haveLaser[w] = 0
                laserCoord = dict(wormCoords[w][HEAD])
                while isWithinGrid(laserCoord):
                    if direction[w] == UP:
                        laserCoord['y'] -= 1
                    elif direction[w] == DOWN:
                        laserCoord['y'] += 1
                    elif direction[w] == LEFT:
                        laserCoord['x'] -= 1
                    elif direction[w] == RIGHT:
                        laserCoord['x'] += 1
                    
                    laserBeam.append(dict(laserCoord))


        DISPLAYSURF.fill(BGCOLOR)
        drawGrid()
        for w in range(len(wormCoords)):
            drawWorm(wormCoords[w], haveLaser[w])
        
        for l in range(len(haveLaser)):
            if haveLaser[l] > 0:
                haveLaser[l] -= 1

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

def getActions(wormCoords, direction, apples):
    # Move with some randomness
    # Go toward apples if within sensing radius
    # Don't hit walls
    prob_dirchange = 0.5
    newDir = direction
    # Randomness
    for d in range(len(newDir)):
        change = random.randint(0,1)
        bounds = getBoundaries(d, len(newDir))
        changeDir = random.uniform(0,1) < prob_dirchange
        sa = senseApple(wormCoords[d][HEAD], apples)
        # beyond corners
        if wormCoords[d][HEAD]['x'] <= bounds['xmin'] and wormCoords[d][HEAD]['y'] <= bounds['ymin']:
            if direction[d] == UP:
                newDir[d] = RIGHT
            elif direction[d] == LEFT:
                newDir[d] = DOWN

        elif wormCoords[d][HEAD]['x'] <= bounds['xmin'] and wormCoords[d][HEAD]['y'] >= bounds['ymax']:
            if direction[d] == DOWN:
                newDir[d] = RIGHT
            elif direction[d] == LEFT:
                newDir[d] = UP

        elif wormCoords[d][HEAD]['x'] >= bounds['xmax'] and wormCoords[d][HEAD]['y'] <= bounds['ymin']:
            if direction[d] == UP:
                newDir[d] = LEFT
            elif direction[d] == RIGHT:
                newDir[d] = DOWN

        elif wormCoords[d][HEAD]['x'] >= bounds['xmax'] and wormCoords[d][HEAD]['y'] >= bounds['ymax']:
            if direction[d] == DOWN:
                newDir[d] = LEFT
            elif direction[d] == RIGHT:
                newDir[d] = UP

        # out of bounds
        elif wormCoords[d][HEAD]['x'] < bounds['xmin']:
            if direction[d] == LEFT:
                if change == 0:
                    newDir[d] = UP
                elif change == 1:
                    newDir[d] = DOWN
            elif direction[d] == UP or direction[d] == DOWN:
                newDir[d] = RIGHT

        elif wormCoords[d][HEAD]['x'] > bounds['xmax']:
            if direction[d] == RIGHT:
                if change == 0:
                    newDir[d] = UP
                elif change == 1:
                    newDir[d] = DOWN
            elif direction[d] == UP or direction[d] == DOWN:
                newDir[d] = LEFT

        elif wormCoords[d][HEAD]['y'] < bounds['ymin']:
            if direction[d] == UP:
                if change == 0:
                    newDir[d] = LEFT
                elif change == 1:
                    newDir[d] = RIGHT
            elif direction[d] == LEFT or direction[d] == RIGHT:
                newDir[d] = DOWN

        elif wormCoords[d][HEAD]['y'] > bounds['ymax']:
            if direction[d] == DOWN:
                if change == 0:
                    newDir[d] = LEFT
                elif change == 1:
                    newDir[d] = RIGHT
            elif direction[d] == LEFT or direction[d] == RIGHT:
                newDir[d] = UP

        # on bounds
        elif wormCoords[d][HEAD]['x'] == bounds['xmin']:
            if direction[d] == LEFT:
                if change == 0:
                    newDir[d] = UP
                elif change == 1:
                    newDir[d] = DOWN
            elif direction[d] == UP or direction[d] == DOWN:
                if changeDir and change == 1:
                    newDir[d] = RIGHT

        elif wormCoords[d][HEAD]['x'] == bounds['xmax']:
            if direction[d] == RIGHT:
                if change == 0:
                    newDir[d] = UP
                elif change == 1:
                    newDir[d] = DOWN
            elif direction[d] == UP or direction[d] == DOWN:
                if changeDir and change == 0:
                    newDir[d] = LEFT

        elif wormCoords[d][HEAD]['y'] == bounds['ymin']:
            if direction[d] == UP:
                if change == 0:
                    newDir[d] = LEFT
                elif change == 1:
                    newDir[d] = RIGHT
            elif direction[d] == LEFT or direction[d] == RIGHT:
                if changeDir and change == 1:
                    newDir[d] = DOWN

        elif wormCoords[d][HEAD]['y'] == bounds['ymax']:
            if direction[d] == DOWN:
                if change == 0:
                    newDir[d] = LEFT
                elif change == 1:
                    newDir[d] = RIGHT
            elif direction[d] == LEFT or direction[d] == RIGHT:
                if changeDir and change == 0:
                    newDir[d] = UP

        elif sa != {}:
            if sa['x'] < 0 and sa['y'] <= 0 and direction[d] != RIGHT:
                newDir[d] = LEFT
            elif sa['x'] >= 0 and sa['y'] < 0 and direction[d] != DOWN:
                newDir[d] = UP
            elif sa['x'] > 0 and sa['y'] >= 0 and direction[d] != LEFT:
                newDir[d] = RIGHT
            elif sa['x'] <= 0 and sa['y'] > 0 and direction[d] != UP:
                newDir[d] = DOWN

        elif changeDir:
            if direction[d] == UP or direction[d] == DOWN:
                if change == 0:
                    newDir[d] = LEFT
                elif change == 1:
                    newDir[d] = RIGHT
            elif direction[d] == LEFT or direction[d] == RIGHT:
                if change == 0:
                    newDir[d] = UP
                elif change == 1:
                    newDir[d] = DOWN

    return newDir

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

def getBoundaries(num, count):
    bounds = {}
    if not CENTRALIZED:
        bounds['xmin'] = 0
        bounds['xmax'] = CELLWIDTH - 1
        bounds['ymin'] = 0
        bounds['ymax'] = CELLHEIGHT - 1
    elif CENTRALIZED:
        a = 0
        b = 0
        for n in range(30):
            a = n ** 2
            if a > count:
                break
            else:
                b = a

        
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