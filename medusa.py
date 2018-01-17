# Wormy (a Nibbles clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

import random, pygame, sys
from pygame.locals import *

FPS = 10
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

NUM_WORMS = 2 # number of worms
NUM_APPLES = 2
LASER_FREQ = 0.07
LASER_FULL_CHARGE = 30

def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT

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
    for _ in range(NUM_WORMS):
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
    for a in range(NUM_APPLES):
        apples.append(getRandomLocation())

    laserPickup = False

    while True: # main game loop
        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                # Controls worm 1
                if (event.key == K_LEFT) and direction[0] != RIGHT:
                    direction[0] = LEFT
                elif (event.key == K_RIGHT) and direction[0] != LEFT:
                    direction[0] = RIGHT
                elif (event.key == K_UP) and direction[0] != DOWN:
                    direction[0] = UP
                elif (event.key == K_DOWN) and direction[0] != UP:
                    direction[0] = DOWN
                elif event.key == K_ESCAPE:
                    terminate()
                elif (event.key == K_KP1):
                    fireLaser[0] = True
                else:
                    fireLaser[0] = False

                # Controls worm 2
                if (event.key == K_a) and direction[1] != RIGHT:
                    direction[1] = LEFT
                elif (event.key == K_d) and direction[1] != LEFT:
                    direction[1] = RIGHT
                elif (event.key == K_w) and direction[1] != DOWN:
                    direction[1] = UP
                elif (event.key == K_s) and direction[1] != UP:
                    direction[1] = DOWN
                elif (event.key == K_e):
                    fireLaser[1] = True
                else:
                    fireLaser[1] = False

                # Controls all worms
                for d in range(NUM_WORMS):
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
                    #else:
                    #    fireLaser[d] = False

        hit_gameover = -1
        for w in range(NUM_WORMS):
            # check if the worm has hit itself, the edge, or a stone
            if not isWithinGrid(wormCoords[w][HEAD]) or wormCoords[w][HEAD] in stones:
                hit_gameover = w # game over
            for wormBody in wormCoords[w][1:]:
                if wormBody['x'] == wormCoords[w][HEAD]['x'] and wormBody['y'] == wormCoords[w][HEAD]['y']:
                    hit_gameover = w # game over
            # or another worm
            for wother in range(NUM_WORMS):
                if wother == w:
                    continue
                for indivWormCoords in wormCoords[wother]:
                    if wormCoords[w][HEAD]['x'] == indivWormCoords['x'] and wormCoords[w][HEAD]['y'] == indivWormCoords['y']:
                        hit_gameover = w
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

            # check if worm has eaten an apple
            if wormCoords[w][HEAD] in apples:
                apples.remove(wormCoords[w][HEAD])
                loc = getRandomLocation()
                while loc in stones:
                    loc = getRandomLocation()
                apples.append(loc) # set a new apple somewhere
                gotApples[w] = True
            else:
                gotApples[w] = False
                # don't remove worm's tail segment
            
        

        # discard old laser beam coordinates
        laserBeam = []
        for w in range(NUM_WORMS):
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
        for w in range(NUM_WORMS):
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

        scores = []
        for w in range(NUM_WORMS):
            if w == hit_gameover:
                scores.append(len(wormCoords[w]) - 5)
            else:
                scores.append(len(wormCoords[w]) - 3)
        drawScores(scores)
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

def drawScores(scores):
    scoreStr = ''
    for i in range(len(scores)):
        scoreStr += 'W' + str(i) + ' score: ' + str(scores[i]) + ' '
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