#!/usr/bin/env python
#print("moves:",moves,end='\r', flush=True)
#notes: check all playfield[v][h] in all versions to make sure v comes first.  I found one where it was switched
#       and this may account for when the zombie dots don't die
# - ship objects that also have a sprite should have
#   their HV co-ordinates looked at.  We want to draw the sprite around the center of the sprite, not the corner
#   Look at SpaceDot homing missile for an example.
#------------------------------------------------------------------------------



#------------------------------------------------------------------------------
#                                                                            --
#  ____  _____ _____ _____ _   _ ____  _____ ____                            --
# |  _ \| ____|  ___| ____| \ | |  _ \| ____|  _ \                           --
# | | | |  _| | |_  |  _| |  \| | | | |  _| | |_) |                          --
# | |_| | |___|  _| | |___| |\  | |_| | |___|  _ <                           --
# |____/|_____|_|   |_____|_| \_|____/|_____|_| \_\                          --                                                                            --
#                                                                            --
#------------------------------------------------------------------------------



#------------------------------------------------------------------------------
#  Arcade Retro Clock RGB
#  
#  Copyright 2021 William McEvoy
#  Metropolis Dreamware Inc.
#  william.mcevoy@gmail.com
#
#  NOT FOR COMMERCIAL USE
#  If you want to use my code for commercial purposes, contact William McEvoy
#  and we can make a deal.
#
#
#------------------------------------------------------------------------------
#   Version: 0.1                                                             --
#   Date:    January 15, 2022                                                --
#   Reason:  Converted to use LEDarcade                                      --
#------------------------------------------------------------------------------



#------------------------------------------------------------------------------
# Initialization Section                                                     --
#------------------------------------------------------------------------------
from __future__ import print_function


import LEDarcade as LED
import copy
import random
import time
import numpy
import math
from datetime import datetime, timedelta
from rgbmatrix import graphics




random.seed()
start_time = time.time()






#-----------------------------
# Defender Global Variables --
#-----------------------------

#Sprite display locations
ClockH,      ClockV,      ClockRGB      = 0,0,  (0,150,0)
DayOfWeekH,  DayOfWeekV,  DayOfWeekRGB  = 0,6,  (150,0,0)
MonthH,      MonthV,      MonthRGB      = 0,12, (0,20,200)
DayOfMonthH, DayOfMonthV, DayOfMonthRGB = 2,18, (100,100,0)
CurrencyH,   CurrencyV,   CurrencyRGB   = 0,27, (0,150,0)

#Sprite filler tuple
SpriteFillerRGB = (0,4,0)

#GroundRGB = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
DirtGreen     = (0,24,0)
SurfaceGreen  = (0,50,0)
DirtYellow    = (24,24,0)
SurfaceYellow = (24,24,0)
DirtPurple    = (20,0,20)
SurfacePurple = (20,0,20)
DirtOrange    = (30,10,0)
SurfaceOrange = (50,30,0)

GroundColorList = ((DirtGreen,SurfaceGreen),
                   (DirtYellow,SurfaceYellow),
                   (DirtPurple,SurfacePurple),
                   (DirtOrange,SurfaceOrange)
                  )
GroundColorCount = 4


DefenderWorldWidth = 2048
HumanCount         = 25
EnemyShipCount     = 20
SpawnNewEnemiesTargetCount = 10

#Movement
DefenderMoveUpRate   = 3
DefenderMoveDownRate = 3
HumanMoveChance      = 2

#Gravity
GroundParticleGravity  = 0.05
EnemyParticleGravity   = 0.0198
BombGravity            = 0.0198



#Bomb
DefenderBombVelocityH =  0.4
DefenderBombVelocityV = -0.2


#---------------------------------------
#Variable declaration section
#---------------------------------------
ScrollSleep         = 0.025
TerminalTypeSpeed   = 0.02  #pause in seconds between characters
TerminalScrollSpeed = 0.02  #pause in seconds between new lines
CursorRGB           = (0,255,0)
CursorDarkRGB       = (0,50,0)


BrightRGB  = (0,200,0)
ShadowRGB  = (0,5,0)
ShowCrypto = 'N'
KeyboardSpeed   = 500
CheckClockSpeed = 500

CheckTime        = 60
random.seed()
start_time = time.time()





#------------------------------
# Sprites, Arrays, Functions --
#------------------------------



  



def ScanInFrontOfDefender(H,V,Defender,DefenderPlayfield):
  
  ScanDirection = 2
  ScanH         = Defender.h + Defender.width  #start in front of ship
  ScanV         = Defender.v
    
  Item          = ''
  ItemList      = ['NULL']
  RadarRange    = 50
  
  # x 1234567890...50
  
  
  try:

    for x in range(0,RadarRange):
      ScanH, ScanV = LED.CalculateDotMovement(ScanH,ScanV,ScanDirection)
      if(ScanH + H < DefenderPlayfield.width):
        Item = DefenderPlayfield.map[ScanV + V][ScanH + H].name
        ItemList.append(Item)
        break
  except:
    print("ERROR at location:",ScanV + V, ScanH + H)
  

    

  return ItemList



def ScanFarAway(H,V,Defender,DefenderPlayfield):
  #HV are the current upper left hand corner of the displayed playfield window
  ScanDirection = 2
  ScanH         = Defender.h + Defender.width  #start in front of ship
  ScanV         = Defender.v
  Item          = ''
  ItemList      = [('EmptyObject',0,0)]
  RadarStart    = 10
  RadarStop     = 50
  
  # x 20...50
  
 
  try:
    found = False
    for x in range(RadarStart,RadarStop):
      ScanH, ScanV = LED.CalculateDotMovement(ScanH,ScanV,ScanDirection)
      if(ScanH + H < DefenderPlayfield.width):
        
        if(DefenderPlayfield.map[ScanV + V][ScanH + H].alive == True):
          Item = DefenderPlayfield.map[ScanV + V][ScanH + H].name
          ItemList.append((Item,ScanH,ScanV))
          found = True
          break

  except:
    print("ERROR at location:",ScanV + V, ScanH + H)

  return ItemList



def LookForTargets(H,V,TargetName,Defender, DefenderPlayfield,Canvas):
  #HV are the current upper left hand corner of the displayed playfield window
  EnemyName = 'EmptyObject'
  EnemyH    = -1
  EnemyV    = -1

  #To improve performance, we will not scan every pixel in radar range
  #Radar scanning will be interlaced
  #This procedure is called continuously so lets scan a net instead of a solid area
  #The size of the holes in the net is determined by ScanStep
  StartX    = LED.HatWidth -1
  StopX     = 10
  StartY    = 0
  StopY     = LED.HatHeight -1
  ScanStep  = 3
  
  #Add a bit of randomness to the vertical start pixel
  if random.randint(0,1) == 1:
    StartY = 1

  try:

    #Look at furthest part of the screen and start checking for enemies
    x = 0
    y = 0
    
    #Adjust StartX if it is too close to the end of the playfield
    if (LED.HatWidth + H >= DefenderPlayfield.width):
      StartX =  LED.HatWidth - (LED.HatWidth + H -DefenderPlayfield.width)
  
    #If an enemy is on screen, take note and exit the loops
    #sprites are usually bigger than a dot, so we use range step to increase speed of scan
    Found = False
    for x in range (StartX,0,-ScanStep):
      #print(DefenderPlayfield.map[y][x].name)
      for y in range(StartY,StopY,ScanStep):

        if(DefenderPlayfield.map[y][x + H - 1].name == TargetName and DefenderPlayfield.map[y][x + H - 1].alive == True):
          
          if(DefenderPlayfield.map[y][x + H - 1].v < Defender.v):
            #we do randint to stop the jitteriness of ship moving up and down
            if(random.randint(0,DefenderMoveUpRate) == 1):
              Defender.v = Defender.v - 1
            Found = True
            break
          elif(DefenderPlayfield.map[y][x + H -1].v > Defender.v):
            if(random.randint(0,DefenderMoveDownRate) == 1):
              Defender.v = Defender.v + 1
            Found = True
            break
      if(Found == True):
        break


  except:
    print("ERROR at location: xy H StartX x+H",x,y,StartX,x+H)
    print("A stupid error has occurred when finding targets.  Please fix this soon.")

  
  #If an target was found, scan to see if it is in firing range
  if(Found == True):
    ItemList = ScanFarAway(H,V,Defender,DefenderPlayfield)
    EnemyTargets = ['Human','EnemyShip']

    
    #print(ItemList)
    
    for i in range (0,len(ItemList)):
      EnemyName,EnemyH, EnemyV = ItemList[i]
      if(EnemyName in EnemyTargets):
        break
    

  return EnemyName,EnemyH, EnemyV
      

    #if ( any(item in EnemyTargets for item,h,v in ItemList)):
      #for x in range (0,45):
      #  LED.setpixel(Defender.h + 5 + x,Defender.v + 2,255,0,0)




def ShootTarget(PlayfieldH, PlayfieldV, TargetName, TargetH,TargetV,Defender, DefenderPlayfield,Canvas):
  #PlayfieldH is the upper left hand corner of the playfield window being displayed
  #TargetH and TargetV are on screen co-ordinates (64x32)
  #print("TargetName:",TargetName)
  #print("Shooting:",DefenderPlayfield.map[TargetV][TargetH+PlayfieldH].name)
  graphics.DrawLine(Canvas,Defender.h + 5, Defender.v +2, TargetH, TargetV +2, graphics.Color(255,0,0))
  DefenderPlayfield.map[TargetV][TargetH+PlayfieldH].alive = False
  DefenderPlayfield.map[TargetV][TargetH+PlayfieldH].EraseSpriteFromPlayfield(DefenderPlayfield)
  #print("Convert to particles")
  DefenderPlayfield.map[TargetV][TargetH+PlayfieldH].ConvertSpriteToParticles()


  return DefenderPlayfield 



def ShootGround(PlayfieldH, PlayfieldV, Defender, DefenderPlayfield, Ground, Canvas):
  #PlayfieldH is the upper left hand corner of the playfield window being displayed

  ScanH = Defender.h + 3 
  ScanV = Defender.v + 2

  if(ScanH + PlayfieldH < DefenderPlayfield.width):
    #find ground under defender
    for i in range (ScanV, LED.HatHeight):
      if Ground.map[i][ScanH + PlayfieldH] != (0,0,0):
        graphics.DrawLine(Canvas,ScanH, ScanV, ScanH, i, graphics.Color(200,200,0))
        Ground.map[i][ScanH + PlayfieldH] = (0,0,0)
        if(i+1 < LED.HatHeight):
          Ground.map[i+1][ScanH + PlayfieldH] = (150,0,0)
        break


   


  return DefenderPlayfield, Ground



def DebugPlayfield(Playfield,h,v,width,height):
  #Show contents of playfield - in text window, for debugging purposes
    
  print ("Map width height:",width,height)

  
  print ("===============================================================")

  for V in range(0,height):
    for H in range (0,width):
       
      name = Playfield[V+v][H+h].name
      #print ("Display: ",name,V,H)
      if (name == 'EmptyObject'):
        print ('  ',end='')

      #draw border walls
        
      #draw interior
      elif (name == 'Wall'):
        print (' #',end='')

      elif (name == 'Ground'):
        print (' G',end='')

        

      #draw Human
      elif (name == 'Human'):
        print (' H',end='')

      #draw EnemyShip
      elif (name == 'EnemyShip'):
        print ('**',end='')




      #draw interior
      elif (name == 'WallBreakable'):
        print (' o',end='')

      elif (Playfield[V][H].alive == 1):
        print (' ?',end='')
        #print ("Name?:",name," alive:",Playfield[V][H].alive)
      elif (Playfield[V][H].alive == 0):
        print (' !',end='')
        #print ("Name!:",name," alive:",Playfield[V][H].alive)
      else:
        print (' X',end='')
        #print ("NameX:",name," alive:",Playfield[V][H].alive)

    print('')
  print ("=============================================")


  return

    

def CreateHumans(HumanCount,Ground,DefenderPlayfield):

  Humans = []

  #humans must be located at least HatWidth from the start
  for count in range (0,HumanCount):
    
    #LED.HumanSprite.framerate = random.randint(15,50)
    
    TheSprite = LED.HumanSprite
    TheSprite.h         = random.randint(63,DefenderWorldWidth)
    TheSprite.v         = random.randint(16,LED.HatHeight-1)
    
    if(random.randint(0,1) == 1):
      TheSprite.direction = 1
    else:
      TheSprite.direction = -1
    
    Humans.append(copy.deepcopy(TheSprite))
    print("Placing humans:",count)
    DefenderPlayfield.CopyAnimatedSpriteToPlayfield(Humans[count].h,Humans[count].v,Humans[count])
  
  return Humans, DefenderPlayfield


def CreateEnemyWave(ShipCount,Ground,DefenderPlayfield,Canvas):
  global EnemyShipCount

  EnemyShipCount = ShipCount
  EnemyShips = []
  ShipType = random.randint(0,27)
  for count in range (0,ShipCount):
    NewSprite = copy.deepcopy(LED.ShipSprites[ShipType])
    NewSprite.framerate = random.randint(2,12)
    NewSprite.name = "EnemyShip"
    EnemyShips.append(NewSprite)
    #EnemyShips[count].ConvertSpriteToParticles()

    EnemyAliveCountSprite = LED.CreateBannerSprite(str(len(EnemyShips)))
    Canvas = LED.CopySpriteToCanvasZoom(EnemyAliveCountSprite,1,2,(0,0,150),(0,0,0),ZoomFactor = 1,Fill=False,Canvas=Canvas)
    Canvas = LED.TheMatrix.SwapOnVSync(Canvas)


    Finished = False
    while (Finished == False):
      #Find a spot in the sky for the ship
      h = random.randint(64,DefenderWorldWidth)
      v = random.randint(1,LED.HatHeight-1)

      try:

        if(Ground.map[v][h] == (0,0,0)):
          EnemyShips[count].h = h
          EnemyShips[count].v = v
          
          Finished = True
          print("Placing EnemyShips:",count)
          DefenderPlayfield.CopyAnimatedSpriteToPlayfield(EnemyShips[count].h,EnemyShips[count].v,EnemyShips[count])

      except:
        print("Error placing ship HV",h,v)

  return EnemyShips,DefenderPlayfield



def AddEnemyShips(EnemyShips,ShipCount,Ground,DefenderPlayfield,Canvas):
  global EnemyShipCount

    
  ShipType = random.randint(0,27)
  for count in range (0,ShipCount):
    NewSprite = copy.deepcopy(LED.ShipSprites[ShipType])
    NewSprite.framerate = random.randint(2,12)
    NewSprite.name = "EnemyShip"
    EnemyShips.append(NewSprite)
    #EnemyShips[count].ConvertSpriteToParticles()

    EnemyAliveCountSprite = LED.CreateBannerSprite(str(len(EnemyShips)))
    Canvas = LED.CopySpriteToCanvasZoom(EnemyAliveCountSprite,1,2,(0,0,150),(0,0,0),ZoomFactor = 1,Fill=False,Canvas=Canvas)
    Canvas = LED.TheMatrix.SwapOnVSync(Canvas)



    Finished = False
    while (Finished == False):
      #Find a spot in the sky for the ship
      h = random.randint(64,DefenderWorldWidth)
      v = random.randint(1,LED.HatHeight-1)

      try:

        if(Ground.map[v][h] == (0,0,0)):
          EnemyShips[count].h = h
          EnemyShips[count].v = v
          
          Finished = True
          print("Placing EnemyShips:",count)
          DefenderPlayfield.CopyAnimatedSpriteToPlayfield(EnemyShips[count].h,EnemyShips[count].v,EnemyShips[count])

      except:
        print("Error placing ship HV",h,v)
    
    #Update total enemy count
    EnemyShipCount = len(EnemyShips)

  return EnemyShips, DefenderPlayfield


def AddGroundParticles(h,v,r,g,b,GroundParticles):
    #particles don't interact with anything other than the ground so
    #they are HV co-ordinates that match the display, not the playfield
    NewParticle = LED.Ship(h, v,r,g,b,2,2,2,1,1,'ground',0,0)
    #NewParticle.velocityH = random.random() * (random.randint(0,1) *2 -1) / 5
    NewParticle.velocityH = random.random() * -2 
    NewParticle.velocityV = random.random() * -2
    NewParticle.alive = True
    GroundParticles.append(NewParticle)
    return GroundParticles
    


def DetonateBomb(PlayfieldH,PLayfieldV,DefenderBomb,Ground,GroundParticles,DefenderPlayfield,Canvas):

  # PlayfieldH, PlayfieldV = upper left hand corner of the window being displayed

  bh = round(DefenderBomb.h)
  bv = round(DefenderBomb.v)
  BlastStrength = random.randint(4,10)


  if(bv >= LED.HatHeight -2):
    bv = LED.HatHeight -2
  if(bh + PlayfieldH >= DefenderPlayfield.width -1):
    bh = 0

  

  #Blow up bomb if it touches ground
  #try:
  #blow up pieces of ground
  if(Ground.map[bv][bh+PlayfieldH] != (0,0,0)):

    #r,g,b = (random.randint(50,255),0,0)


    
    #destroy ground
    gv = bv
    gh = bh+PlayfieldH
    for j in range (-2,BlastStrength):
      for i in range (-BlastStrength + j ,BlastStrength - j   ):

        #near to the blast gets erased
        if(gv + j < LED.HatHeight and gh + i < Ground.width):
          Ground.map[gv +j][gh +i] = (0,0,0)
        else:
          break
      
      #set ground outside the blase zone to different color

      if (j >= 0):         
        if(gv + j < LED.HatHeight and (gh + BlastStrength + j) < Ground.width):
          if(Ground.map[gv +j][gh - BlastStrength +j - 1] != (0,0,0)):
            Ground.map[gv +j][gh - BlastStrength +j - 1] = (0,25,0)
          
          if(Ground.map[gv +j][gh + BlastStrength -j ] != (0,0,0)):
            Ground.map[gv +j][gh + BlastStrength -j ] = (0,25,0)
          
      

      #beside blast gets colored green
          
      #Ground.map[gv +j][gh +i -j + 1] = (0,35,0)
      #Ground.map[gv +j][gh +i -j - 1] = (0,35,0)


    #Big white flash
    for i in range (1,BlastStrength):
      graphics.DrawCircle(Canvas,bh,bv,i,graphics.Color(255,255,255))

    #Explode Ground
    for i in range(0,BlastStrength):
      GroundParticles = AddGroundParticles(bh,bv,sr,sg,sb,GroundParticles)

    
    DefenderBomb.alive = False
    #print ("Bomb Dead.",DefenderBomb.alive)

  #except:
  #  print("Error detonating bomb HV velocityV: ",bh+PlayfieldH,bv,DefenderBomb.velocityV)
                
  return DefenderBomb, GroundParticles, Ground, DefenderPlayfield


def MoveGroundParticles (GroundParticles,Canvas):
  #Move ground particles (exploding bomb)
  ParticleCount = len(GroundParticles)
  if(ParticleCount > 0):
    for i in range (0,ParticleCount):
      #print("Particles:",len(GroundParticles))

      if(GroundParticles[i].alive == True):
        GroundParticles[i].UpdateLocationWithGravity(GroundParticleGravity)
        gph = GroundParticles[i].h
        gpv = GroundParticles[i].v
        
        #print("Particle location:",gph,gpv)
    
        #only display particles on screen
        r  = GroundParticles[i].r
        g  = GroundParticles[i].g
        b  = GroundParticles[i].b
        Canvas.SetPixel(gph,gpv,r,g,b)
          
      #kill the particle if they go off the screen
      else:
        GroundParticles[i].alive == False




def PlayDefender(GameMaxMinutes):      
 
  global EnemyShipCount

  finished           = 'N'
  LevelCount         = 0
  EnemyAliveCount    = 0
  OldEnemyAliveCount = 0

  ClockSprite         = LED.CreateClockSprite(24)
  DayOfWeekSprite     = LED.CreateDayOfWeekSprite()
  MonthSprite         = LED.CreateMonthSprite()
  DayOfMonthSprite    = LED.CreateDayOfMonthSprite()

  ClockSprite.on      = 0


  DefenderPlayfield = LED.PlayField(
      name   = "DefenderWorld",
      width  = DefenderWorldWidth,
      height = LED.HatHeight,
      h      = 0,
      v      = 0
    )




  LED.TheMatrix.Clear()
  LED.Canvas.Clear()
  
  Canvas = LED.TheMatrix.CreateFrameCanvas()
  Canvas.Fill(0,0,0)
  Canvas = LED.TheMatrix.SwapOnVSync(Canvas)



  #The map is an array of a lists.  You can address each element has VH e.g. [V][H]
  #Copying the map to the playfield needs to follow the exact same shape



  #----------------------
  #-- Prepare Level    --
  #----------------------
  print("")
  print("")
  print("*****************************************************")
  #LED.OutbreakGamesPlayed = LED.OutbreakGamesPlayed + 1
  #LED.SaveConfigData()
  print("*****************************************************")

  
  




  #--------------------------------
  #-- Create Layers              --
  #--------------------------------

  Background   = LED.Layer(name="backround", width=2048, height=32,h=0,v=0)
  Middleground = LED.Layer(name="backround", width=2048, height=32,h=0,v=0)
  Foreground   = LED.Layer(name="backround", width=2048, height=32,h=0,v=0)
  Ground       = LED.Layer(name="ground",    width=DefenderWorldWidth, height=32,h=0,v=0)


  Background.CreateStars(5,0,50,50)
  Middleground.CreateStars(0,0,100,100)
  Foreground.CreateStars(0,0,200,200)

  
  i = random.randint(0,GroundColorCount -1)
  GroundRGB, SurfaceRGB      = GroundColorList[i]
  GroundR,GroundG,GroundB    = GroundRGB
  SurfaceR,SurfaceG,SurfaceB = SurfaceRGB

    
  Ground.CreateMountains(GroundRGB,SurfaceRGB,maxheight=16)
  
  
  
  #--------------------------------
  #-- Create Enemies             --
  #--------------------------------


    

  Humans,     DefenderPlayfield = CreateHumans(HumanCount=HumanCount, Ground=Ground,DefenderPlayfield=DefenderPlayfield )
  EnemyShips, DefenderPlayfield = CreateEnemyWave(ShipCount=EnemyShipCount, Ground=Ground,DefenderPlayfield=DefenderPlayfield, Canvas = Canvas)
  
  DefenderBomb = LED.BombSprite
  DefenderBomb.alive = False
  DefenderBomb.velocityH = 0
  DefenderBomb.velocityV = 0

  GroundParticles = []


  #--------------------------------
  #-- Main timing loop           --
  #--------------------------------


  x = 0


  #Canvas2 = LED.TheMatrix.CreateFrameCanvas()
  #Canvas2.Fill(22,0,0)
  
  

  while (finished == "N"):
    
    count  = 0
    bx     = 0
    mx     = 0
    fx     = 0
    gx     = -1
    bwidth = Background.width    - LED.HatWidth
    mwidth = Middleground.width  - LED.HatWidth
    fwidth = Foreground.width    - LED.HatWidth
    gwidth = Ground.width        - LED.HatWidth
    brate  = 6
    mrate  = 4
    frate  = 2
    grate  = 1
    DisplayH = 0
    DisplayV = 0
    

    Defender = copy.deepcopy(LED.Defender)
    Defender.h = 5
    Defender.v = 20
     


    while(1==1):
      #main counter
      count = count + 1

      
      #check the time once in a while
      if(random.randint(0,1000) == 1):
        if (ClockSprite.hhmm != datetime.now().strftime('%H:%M')):
          ClockSprite = LED.CreateClockSprite(24)
    
        #End game after X seconds
        h,m,s    = LED.GetElapsedTime(start_time,time.time())
        if(m > GameMaxMinutes):
          print("Elapsed Time:  mm:ss",m,s)
          LED.SaveConfigData()
          print("Ending game after",m," minutes")

          LED.ClearBigLED()
          LED.ClearBuffers()
          CursorH = 0
          CursorV = 0
          LED.ScreenArray,CursorH,CursorV = LED.TerminalScroll(LED.ScreenArray,"ALIEN MUTANTS ARE VANQUISHED",CursorH=CursorH,CursorV=CursorV,MessageRGB=(150,0,0),CursorRGB=(0,255,0),CursorDarkRGB=(0,50,0),StartingLineFeed=1,TypeSpeed=TerminalTypeSpeed,ScrollSpeed=TerminalTypeSpeed)
          LED.BlinkCursor(CursorH= CursorH,CursorV=CursorV,CursorRGB=CursorRGB,CursorDarkRGB=CursorDarkRGB,BlinkSpeed=0.5,BlinkCount=2)
          LED.ScreenArray,CursorH,CursorV = LED.TerminalScroll(LED.ScreenArray,"LIVE TO FIGHT ANOTHER DAY",CursorH=CursorH,CursorV=CursorV,MessageRGB=(100,100,0),CursorRGB=(0,255,0),CursorDarkRGB=(0,50,0),StartingLineFeed=1,TypeSpeed=0.005,ScrollSpeed=ScrollSleep)
          LED.BlinkCursor(CursorH= CursorH,CursorV=CursorV,CursorRGB=CursorRGB,CursorDarkRGB=CursorDarkRGB,BlinkSpeed=0.5,BlinkCount=2)
          
          return();






      #Background
      m,r = divmod(count,brate)
      if(r == 0):
        bx = bx + 1
        if(bx > bwidth):
          bx = 0
      #Canvas = Background.PaintOnCanvas(bx,0,Canvas)


      #Middleground
      m,r = divmod(count,mrate)
      if(r == 0):
        mx = mx + 1
        if(mx > mwidth):
          mx = 0
      #Canvas = Middleground.PaintOnCanvas(mx,0,Canvas)

        
      #foreground
      m,r = divmod(count,frate)
      if(r == 0):
        fx = fx + 1
        if(fx > fwidth):
          fx = 0
      #Canvas = Foreground.PaintOnCanvas(fx,0,Canvas)


      #ground / display
      m,r = divmod(count,grate)
      if(r == 0):
        gx = gx + 1
        if(gx >= gwidth + LED.HatWidth ):
          gx = 0
        DisplayH = gx
      #Canvas = Ground.PaintOnCanvas(gx,0,Canvas)


      Canvas = LED.PaintFourLayerCanvas(bx,mx,fx,gx,Background,Middleground,Foreground,Ground,Canvas)
      #Canvas = LED.RunningMan3Sprite.PaintAnimatedToCanvas(-6,14,Canvas)



      #MoveHumans
      for i in range (0,HumanCount):
        if(Humans[i].alive == True):
          if(random.randint(0,HumanMoveChance) == 1):
            
            #move human, but follow ground
            Humans[i].h = Humans[i].h + Humans[i].direction

            #check boundaries
            if(Humans[i].direction == 1):
              if Humans[i].h >= DefenderPlayfield.width -2:
                Humans[i].h = 0
            else:
              if Humans[i].h <= 0:
                Humans[i].h = DefenderPlayfield.width -1


            if(Humans[i].v >= LED.HatHeight -2):
              Humans[i].v = LED.HatHeight -3

            #print(Humans[i].v,Humans[i].h)

            #check ground
            #If hole, move down

            try:
              rgb = Ground.map[Humans[i].v][Humans[i].h + Humans[i].direction]
            except:
              print("i vh",i,Humans[i].v,Humans[i].h + Humans[i].direction,end="\r")



            if(rgb == (0,0,0)):
              #if a hole at the bottom is encountered, run away
              if(Humans[i].v > LED.HatHeight -4):
                Humans[i].direction = Humans[i].direction * -1
              #print("Moving down:",Humans[i].v)
              else:
                Humans[i].v = Humans[i].v + 1
            else:
              if(random.randint(0,HumanMoveChance) == 1):
                Humans[i].v = Humans[i].v -1
            
          
          hH = Humans[i].h
          hV = Humans[i].v
        
          #check if human is in currently displayed area
          if(DisplayH <=  hH  <= (DisplayH + LED.HatWidth)):
            Canvas = Humans[i].PaintAnimatedToCanvas(hH-DisplayH,hV,Canvas)



      #paint EnemyShip on Canvas
      DisplayMaxH = DisplayH + LED.HatWidth

      for i in range (0,EnemyShipCount):
        H = EnemyShips[i].h 
        V = EnemyShips[i].v 

        if(EnemyShips[i].alive == True):
          #check if EnemyShip is in currently displayed area
          if((DisplayH <=  H  <= DisplayMaxH) or
            (DisplayH <=  H + EnemyShips[i].width  <= DisplayMaxH)):

            Canvas = EnemyShips[i].PaintAnimatedToCanvas(H-DisplayH,V,Canvas)
        else:
          #Show particles
            
            for j in range (0, (len(EnemyShips[i].Particles))):

              #MoveParticles
              if (EnemyShips[i].Particles[j].alive == 1):
                EnemyShips[i].Particles[j].UpdateLocationWithGravity(EnemyParticleGravity)
                ph = EnemyShips[i].Particles[j].h
                pv = EnemyShips[i].Particles[j].v

                #only display particles on screen
                if(DisplayH <=  ph  <= DisplayMaxH):
                  r  = EnemyShips[i].Particles[j].r
                  g  = EnemyShips[i].Particles[j].g
                  b  = EnemyShips[i].Particles[j].b
                  #print("Ship Particle:",i,j)  
                  #Canvas.SetPixel(H - DisplayH + random.randint(-3,3),V + random.randint(-3,3),r,g,b)
                  Canvas.SetPixel(ph - DisplayH,pv,r,g,b)
                
                #kill the particle if the go off the screen
                else:
                  EnemyShips[i].Particles[j].alive == 0
                


      
      #--------------------------------
      #-- Move Defender              --
      #--------------------------------

      #defender needs to avoid the ground
      #shoot enemies
      #pick up humans
      


      if(random.randint(0,15) == 1):
        Defender.v = Defender.v -1
      elif(random.randint(0,15) == 1):
        Defender.v = Defender.v +1


      ScanV = Defender.v + 10
      if(ScanV > LED.HatHeight -2):
        ScanV = LED.HatHeight -2

      if(Ground.map[ScanV][gx] != (0,0,0)): 
        if(random.randint(0,5) == 1):
          Defender.v = Defender.v - 1
      else:
        if(random.randint(0,200) == 1):
          Defender.v = Defender.v + 1

      #keep defender within the screen borders
      if(Defender.v >= LED.HatHeight):
        Defender.v = Defender.v -1
      if(Defender.v <= 0):
        Defender.v = 0

      #Find targets and start blasting
      EnemyName, EnemyH, EnemyV = LookForTargets(gx,0, 'EnemyShip',Defender,DefenderPlayfield,Canvas)
      if(EnemyName == 'EnemyShip'):
        #print("Shooting:",EnemyName, EnemyH ,EnemyV)
        DefenderPlayfield = ShootTarget(gx, 0, EnemyName,EnemyH, EnemyV, Defender,DefenderPlayfield,Canvas)
        #graphics.DrawLine(Canvas,Defender.h + 5, Defender.v + 2, Defender.h + 40, Defender.v + 2, graphics.Color(255,0,0));

      #Strafe Ground
      #DefenderPlayfield, Ground = ShootGround(gx,0,Defender, DefenderPlayfield,Ground,Canvas)
      
      Canvas = LED.Defender.PaintAnimatedToCanvas(5,Defender.v,Canvas)


      #--------------------------------
      #-- Move Defender Bomb         --
      #--------------------------------

      if(random.randint(0,25) == 1 and DefenderBomb.alive == False):
        #print ("Making Bomb alive",DefenderBomb.alive,DefenderBomb.h,DefenderBomb.v)
        DefenderBomb.alive = True
        DefenderBomb.h = Defender.h + 3
        DefenderBomb.v = Defender.v + 1
        DefenderBomb.velocityH = DefenderBombVelocityH
        DefenderBomb.velocityV = DefenderBombVelocityV

      
      if(DefenderBomb.alive == True):
        #print ("Bomb alive")
        #Move bomb
        DefenderBomb.UpdateLocationWithGravity()
        
        bh = round(DefenderBomb.h)
        bv = round(DefenderBomb.v)

        if(bv >= LED.HatHeight -1):
          bv = LED.HatHeight -1
        if(bh + gx >= DefenderPlayfield.width -1):
          bh = 0
        Canvas = DefenderBomb.PaintAnimatedToCanvas(bh,bv,Canvas)


        #Detonate Bomb if at target
        (DefenderBomb, 
         GroundParticles, 
         Ground, 
         DefenderPlayfield
         )  = DetonateBomb(DisplayH,
                           0,
                           DefenderBomb,
                           Ground,
                           GroundParticles,
                           DefenderPlayfield,
                           Canvas
                           )









      #--------------------------------
      #-- Move Defender Bomb         --
      #--------------------------------
      MoveGroundParticles (GroundParticles,Canvas)







      #--------------------------------
      #-- Numerical Displays         --
      #--------------------------------

      #Add clock
      Canvas = LED.CopySpriteToCanvasZoom(ClockSprite,(LED.HatWidth - ClockSprite.width -2),2,(0,100,0),(0,5,0),1,False,Canvas)


      #Add display
      OldEnemyAliveCount = EnemyAliveCount
      EnemyAliveCount = 0
      for i in range(0,len(EnemyShips)):
        if(EnemyShips[i].alive == True):
          EnemyAliveCount = EnemyAliveCount + 1
      
      #Oncly calculate if the count changes
      if(OldEnemyAliveCount != EnemyAliveCount):
        EnemyAliveCountSprite = LED.CreateBannerSprite(str(EnemyAliveCount))
      Canvas = LED.CopySpriteToCanvasZoom(EnemyAliveCountSprite,1,2,(0,0,150),(0,0,0),ZoomFactor = 1,Fill=False,Canvas=Canvas)








      #--------------------------------
      #-- Add more ships             --
      #--------------------------------

      if(EnemyShipCount < SpawnNewEnemiesTargetCount):
        EnemyShips, DefenderPlayfield = AddEnemyShips(EnemyShips, ShipCount=20, Ground=Ground,DefenderPlayfield=DefenderPlayfield ,Canvas=Canvas)
        


      #--------------------------------
      #-- Display canvas             --
      #--------------------------------

      Canvas = LED.TheMatrix.SwapOnVSync(Canvas)
      
    
      #--------------------------------
      #-- Cleanup the debris         --
      #--------------------------------
      
      #to reduce the amount of objects being tracked we remove old
      #ships, if they are far enough off the screen to not have any
      #particles still bouncing

      #ships and their particles
      DeletedShips = 0
      j = 0
      if(random.randint(0,100) == 1):
        for i in range (0,EnemyShipCount):
          
          #print("i j EnemyShipCount LenEnemyShip:",i,j,EnemyShipCount,len(EnemyShips))
          H = EnemyShips[j].h 
          V = EnemyShips[j].v 
          
          DeleteH = DisplayH - LED.HatWidth
          
          #if enemy is dead and is off screen, nuke them
          if(EnemyShips[j].alive == False):
            #check if EnemyShip is in currently NOT in displayed area
            
            if(H < DeleteH):
              del EnemyShips[j]
              DeletedShips = DeletedShips + 1
              j = j - 1
          
          j = j + 1
              
              #break
        #I did it this way to avoid changing the variable used in a for loop
        EnemyShipCount = EnemyShipCount - DeletedShips
        print("Garbage cleanup EnemyShipCount:",EnemyShipCount)
        
              
      #delete ground particles
      j = 0
      if(random.randint(0,50) == 1):
        GroundParticleCount = len(GroundParticles)
        if(GroundParticleCount >= 1):

          for i in range (0,GroundParticleCount):
            H = GroundParticles[j].h 
            V = GroundParticles[j].v 
            
            DeleteH = DisplayH -1
            
            #if enemy is dead and is off screen, nuke them
            if(H < DeleteH):
              del GroundParticles[j]
              j = j - 1
            
            j = j + 1
                

      #delete old bomb
      if (DefenderBomb.v >= 30):
        DefenderBomb.alive = False
          
          







      #if(random.randint(0,50) == 1):
      #  DebugPlayfield(DefenderPlayfield.map,gx,0,64,32)




  #let the display show the final results before clearing
  time.sleep(1)
  LED.ClearBigLED()

  return






























def LaunchDefender(GameMaxMinutes = 10000):
  
    PlayDefender(GameMaxMinutes)
    
    #--------------------------------------
    # M A I N   P R O C E S S I N G      --
    #--------------------------------------

    LED.ShowTitleScreen(
        BigText             = 'SPACE',
        BigTextRGB          = LED.HighRed,
        BigTextShadowRGB    = LED.ShadowRed,
        LittleText          = 'DEFENDER',
        LittleTextRGB       = LED.MedGreen,
        LittleTextShadowRGB = (0,10,0), 
        ScrollText          = 'BRING ON THE MUTANTS',
        ScrollTextRGB       = LED.MedYellow,
        ScrollSleep         = 0.03, # time in seconds to control the scrolling (0.005 is fast, 0.1 is kinda slow)
        DisplayTime         = 1,           # time in seconds to wait before exiting 
        ExitEffect          = 0            # 0=Random / 1=shrink / 2=zoom out / 3=bounce / 4=fade /5=fallingsand
        )


    LED.ClearBigLED()
    LED.ClearBuffers()
    CursorH = 0
    CursorV = 0
    LED.ScreenArray,CursorH,CursorV = LED.TerminalScroll(LED.ScreenArray,"CONNECTING TO DEEP SPACE ARRAY",CursorH=CursorH,CursorV=CursorV,MessageRGB=(100,100,0),CursorRGB=(0,255,0),CursorDarkRGB=(0,50,0),StartingLineFeed=1,TypeSpeed=TerminalTypeSpeed,ScrollSpeed=TerminalTypeSpeed)
    LED.BlinkCursor(CursorH= CursorH,CursorV=CursorV,CursorRGB=CursorRGB,CursorDarkRGB=CursorDarkRGB,BlinkSpeed=0.5,BlinkCount=2)
    LED.ScreenArray,CursorH,CursorV = LED.TerminalScroll(LED.ScreenArray,"TRANSMITTING COORDINATES",CursorH=CursorH,CursorV=CursorV,MessageRGB=(100,100,0),CursorRGB=(0,255,0),CursorDarkRGB=(0,50,0),StartingLineFeed=1,TypeSpeed=TerminalTypeSpeed,ScrollSpeed=TerminalTypeSpeed)
    LED.BlinkCursor(CursorH= CursorH,CursorV=CursorV,CursorRGB=CursorRGB,CursorDarkRGB=CursorDarkRGB,BlinkSpeed=0.5,BlinkCount=2)
    LED.ScreenArray,CursorH,CursorV = LED.TerminalScroll(LED.ScreenArray,"DESTROY ALL INVADERS!",CursorH=CursorH,CursorV=CursorV,MessageRGB=(225,0,0),CursorRGB=(0,255,0),CursorDarkRGB=(0,50,0),StartingLineFeed=1,TypeSpeed=0.005,ScrollSpeed=ScrollSleep)
    LED.BlinkCursor(CursorH= CursorH,CursorV=CursorV,CursorRGB=CursorRGB,CursorDarkRGB=CursorDarkRGB,BlinkSpeed=0.5,BlinkCount=2)


    PlayDefender(GameMaxMinutes)
        

    LED.ClearBigLED()
    LED.ClearBuffers()
    CursorH = 0
    CursorV = 0
    LED.ScreenArray,CursorH,CursorV = LED.TerminalScroll(LED.ScreenArray,"MISSION COMPLETE",CursorH=CursorH,CursorV=CursorV,MessageRGB=(0,175,0),CursorRGB=(0,255,0),CursorDarkRGB=(0,50,0),StartingLineFeed=1,TypeSpeed=TerminalTypeSpeed,ScrollSpeed=TerminalTypeSpeed)
    LED.BlinkCursor(CursorH= CursorH,CursorV=CursorV,CursorRGB=CursorRGB,CursorDarkRGB=CursorDarkRGB,BlinkSpeed=0.5,BlinkCount=2)






#execute if this script is called direction
if __name__ == "__main__" :
  while(1==1):
    #LED.LoadConfigData()
    #LED.SaveConfigData()
    print("After SAVE OutbreakGamesPlayed:",LED.OutbreakGamesPlayed)
    LaunchDefender(100000)        


















