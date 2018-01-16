# Wormy (a Nibbles clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

import random, pygame, sys
from pygame.locals import *

FPS = 15
WINDOWWIDTH = 640
WINDOWHEIGHT = 480
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
BGCOLOR = BLACK

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

HEAD = 0 # syntactic sugar: index of the worm's head

NUM_WORMS = 2 # number of worms

def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    pygame.display.set_caption('Wormy')

    showStartScreen()
    while True:
        runGame()
        showGameOverScreen()


def runGame():
    wormCoords = []
    direction = []
    for _ in range(NUM_WORMS):
        # Set a random start point.
        startx = random.randint(5, CELLWIDTH - 6)
        starty = random.randint(5, CELLHEIGHT - 6)
        wormCoords.append([
            {'x': startx,     'y': starty},
            {'x': startx - 1, 'y': starty},
            {'x': startx - 2, 'y': starty}
            ])
        direction.append(RIGHT)

    # Start the apple in a random place.
    apple = getRandomLocation()

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

                # Controls worm 2
                elif (event.key == K_a) and direction[1] != RIGHT:
                    direction[1] = LEFT
                elif (event.key == K_d) and direction[1] != LEFT:
                    direction[1] = RIGHT
                elif (event.key == K_w) and direction[1] != DOWN:
                    direction[1] = UP
                elif (event.key == K_s) and direction[1] != UP:
                    direction[1] = DOWN

        for w in range(NUM_WORMS):
            # check if the worm has hit itself or the edge
            if wormCoords[w][HEAD]['x'] == -1 or wormCoords[w][HEAD]['x'] == CELLWIDTH or wormCoords[w][HEAD]['y'] == -1 or wormCoords[w][HEAD]['y'] == CELLHEIGHT:
                return # game over
            for wormBody in wormCoords[w][1:]:
                if wormBody['x'] == wormCoords[w][HEAD]['x'] and wormBody['y'] == wormCoords[w][HEAD]['y']:
                    return # game over


            # check if worm has eaten an apple
            if wormCoords[w][HEAD]['x'] == apple['x'] and wormCoords[w][HEAD]['y'] == apple['y']:
                # don't remove worm's tail segment
                apple = getRandomLocation() # set a new apple somewhere
            else:
                del wormCoords[w][-1] # remove worm's tail segment

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
            DISPLAYSURF.fill(BGCOLOR)
        drawGrid()
        for w in range(NUM_WORMS):
            drawWorm(wormCoords[w])
        drawApple(apple)
        tot = 0
        for w in range(NUM_WORMS):
            tot += len(wormCoords[w]) - 3
        drawScore(tot)
        pygame.display.update()
        FPSCLOCK.tick(FPS)

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
    titleSurf1 = titleFont.render('Centipedes!', True, PURPLE, YELLOW)
    titleSurf2 = titleFont.render('Centipedes!', True, BLUE)

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
    scoreSurf = BASICFONT.render('Score: %s' % (score), True, WHITE)
    scoreRect = scoreSurf.get_rect()
    scoreRect.topleft = (WINDOWWIDTH - 120, 10)
    DISPLAYSURF.blit(scoreSurf, scoreRect)


def drawWorm(wormCoords):
    for coord in wormCoords:
        x = coord['x'] * CELLSIZE
        y = coord['y'] * CELLSIZE
        wormSegmentRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
        pygame.draw.rect(DISPLAYSURF, DARKGREEN, wormSegmentRect)
        wormInnerSegmentRect = pygame.Rect(x + 4, y + 4, CELLSIZE - 8, CELLSIZE - 8)
        pygame.draw.rect(DISPLAYSURF, GREEN, wormInnerSegmentRect)


def drawApple(coord):
    x = coord['x'] * CELLSIZE
    y = coord['y'] * CELLSIZE
    appleRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
    pygame.draw.rect(DISPLAYSURF, RED, appleRect)


def drawGrid():
    for x in range(0, WINDOWWIDTH, CELLSIZE): # draw vertical lines
        pygame.draw.line(DISPLAYSURF, DARKGRAY, (x, 0), (x, WINDOWHEIGHT))
    for y in range(0, WINDOWHEIGHT, CELLSIZE): # draw horizontal lines
        pygame.draw.line(DISPLAYSURF, DARKGRAY, (0, y), (WINDOWWIDTH, y))


if __name__ == '__main__':
    main()