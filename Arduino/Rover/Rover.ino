/*
This example code for Flutter is
Copyright 2015, Taylor Alexander and Flutter Wireless, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

#include "Flutter.h"

byte myData = 0;
boolean _running = false;
Flutter flutter;

void setup()
{
  Serial.begin(115200);
	SerialUSB.begin(115200);
  while(!SerialUSB);
  
	flutter.band = BAND;
	flutter.setNetworkName("Home network");
	SerialUSB.println("Initializing...");

	if (flutter.init() == true)
	{
		SerialUSB.println("Init success.");
		flutter.ledLightShow();
		delay(500);
	}
	else
	{
		flutter.setLED(RED);
		SerialUSB.println("Init failed.");

		while (true);
	}

	flutter.setAddress(2);
	flutter.connect(1); //form a network with this and one other device
}



void loop()
{
		if(flutter.getState()!=NORMAL_OPERATION) //if we aren't synchronized with another radio, just loop and blink lights.
		{
			if(millis()%400<200)
			{
				flutter.setLED(RED);
			}
			
			else
			{
				flutter.setLED(BLUE);
			}
			
		}
	

	//read the radio to see if there is data available
	if (flutter.dataAvailable() > 0)
	{
		int packetSize = flutter.nextPacketLength();
		byte array[packetSize];
		flutter.readBytes(array, packetSize);
    byte steer = array[6];
    byte throttle = array[7];
    if(SerialUSB.available() > 0)
    {
      while(SerialUSB.read() != -1){};
      SerialUSB.print("Steer: 0x");
      SerialUSB.print(steer,HEX);
      SerialUSB.print(", Throttle: 0x");
      SerialUSB.println(throttle,HEX);
    }
		
		byte j1 = steer;
		byte j2 = throttle;
		//make our LED do nice colors
		j1 = abs((int)j1 - 128) * 1.9f;

		if (j1 < 5)
		{
			j1 = 0;
		}

		if (j2 < 128)
		{
			flutter.setLED(128 - j2, 0, j1);
		}
		else
		{
			flutter.setLED(0, j2 - 128, j1);
		}

		//delay(10);
		flutter.nextPacket();
	}

	//delay(50); //spend some time smelling the roses
}


void button1()
{
	interrupts();
	int val = digitalRead(BUTTON1); //top button

	if (val == HIGH)
	{
		// _button1=255;
	}
	else
	{
		//  _button1=0;
	}

// buttonsChanged=true;
}

void button2()
{
	interrupts();
	int val = digitalRead(BUTTON2);
#ifdef FLUTTER_R2

	if (val == HIGH)
#else
	if (val == LOW)
#endif
	{
		//_button2=255;
	}
	else
	{
		//_button2=0;
	}

// buttonsChanged=true;
}

void systemReset()
{
	flutter.setLED(0, 0, 255);
	delayMicroseconds(16000);
	delayMicroseconds(16000);
	flutter.setLED(0, 0, 0);
	delayMicroseconds(16000);
	delayMicroseconds(16000);
	flutter.setLED(0, 255, 0);
	delayMicroseconds(16000);
	delayMicroseconds(16000);
	flutter.setLED(0, 0, 0);
	delayMicroseconds(16000);
	delayMicroseconds(16000);
	flutter.setLED(255, 0, 0);
	delayMicroseconds(16000);
	delayMicroseconds(16000);
	flutter.setLED(0, 0, 0);
	initiateReset(1);
	tickReset();
}



void radioInterrupt()
{
	flutter.interrupt();
}
void softInt()
{
	flutter.processSoftInt();
}

extern boolean tickInterrupt()
{
	if (!flutter.initialized)
	{
		return true;
	}

	return flutter.tickInt();
}



