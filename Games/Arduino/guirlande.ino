#include <PolychrHAUM.h>

#ifdef BUILD_PC
#define A0 0
#define A1 1
#endif

#define PIN__BTN1          2
#define PIN__BTN2          3
#define PIN__POWER_BTN     4
#define PIN__POWER_CMD     5
#define PIN__POWER_STATUS  6
#define PIN__LEDSTRIP_DATA 10
#define PIN__POTAR_LIGHT   A0
#define PIN__POTAR_SPEED   A1

#define LEDS_NUMBER 150

PolychrHAUM <LEDS_NUMBER, PIN__LEDSTRIP_DATA> khroma;
CRGB gamedata[4][LEDS_NUMBER/4];
LinearAnimator animator;
int curcol = 0;
int add_color = -1;

#ifdef BUILD_PC
CRGB colors[4] = {
	{0xff, 0xff, 0x00},
	{0x00, 0xff, 0xff},
	{0xff, 0x00, 0xff},
	{0xff, 0x00, 0x00},
};
#else
CRGB colors[4] = {
	CRGB::Yellow,
	CRGB::Cyan,
	CRGB::Purple,
	CRGB::Red,
};
#endif

void animate() {
	animator.animate();
	for (int j = 0; j < LEDS_NUMBER/4; ++j) {
		khroma.leds.set_rgb(
			-LEDS_NUMBER/4-(j+int(animator*LEDS_NUMBER/4))%(LEDS_NUMBER/4),
			gamedata[0][j].r,
			gamedata[0][j].g,
			gamedata[0][j].b
		);
		khroma.leds.set_rgb(
			1-LEDS_NUMBER/4+(j+int(animator*LEDS_NUMBER/4))%(LEDS_NUMBER/4),
			gamedata[1][j].r,
			gamedata[1][j].g,
			gamedata[1][j].b
		);
		khroma.leds.set_rgb(
			+LEDS_NUMBER/4-(j+int(animator*LEDS_NUMBER/4))%(LEDS_NUMBER/4),
			gamedata[2][j].r,
			gamedata[2][j].g,
			gamedata[2][j].b
		);
		khroma.leds.set_rgb(
			1+LEDS_NUMBER/4+(j+int(animator*LEDS_NUMBER/4))%(LEDS_NUMBER/4),
			gamedata[3][j].r,
			gamedata[3][j].g,
			gamedata[3][j].b
		);
	}

	int index_in = LEDS_NUMBER/4-1-(int(animator*LEDS_NUMBER/4))%(LEDS_NUMBER/4);
	curcol++;
	curcol %= 4;

	if (khroma.btn1.spressed(true))
		add_color = 0;
	if (khroma.btn1.dpressed(true))
		add_color = 1;
	if (khroma.btn2.spressed(true))
		add_color = 2;
	if (khroma.btn2.dpressed(true))
		add_color = 3;

	if (add_color != -1) {
		gamedata[curcol][index_in] = colors[add_color];
		add_color = -1;
	}
}

void setup() {
	khroma.config_buttons(PIN__BTN1, PIN__BTN2);
	khroma.config_power(PIN__POWER_CMD, PIN__POWER_STATUS, PIN__POWER_BTN);
	khroma.config_light_ctrl(PIN__POTAR_LIGHT);
	khroma.config_speed_ctrl(PIN__POTAR_SPEED);
	khroma.config_animate(animate);
	khroma.setup();

	for (int i = 0; i < 4; ++i) {
		for (int j = 0; j < LEDS_NUMBER/4; ++j) {
			if ((j%9)==0)
				gamedata[i][j] = colors[(i + j)%4];
		}
	}

	animator.set_duration(3000);
	animator.loop(true);
	animator.start();

	khroma.power.poweron();
}

void loop() {
	khroma.loop_step();

#ifndef BUILD_PC
	while (Serial.available()) {
		int input = Serial.read();
		if (input >= '0' && input <= '3') {
			add_color = input - '0';
		} else if (input == 'S') {
			int i, c, g;
			for (g = 0; g < 4; ++g) {
			for (i = 0; i < sizeof(gamedata[0])/sizeof(*gamedata[0]); ++i) {
				for (c = 0; c < 4; ++c) {
					if (colors[c] == gamedata[g][i]) {
						Serial.print(c);
					}
				}
				Serial.print(',');
			}
			}
			Serial.print('\n');
		} else if (input == 'R') {
			char done = 0;
			CRGB* pdata = &gamedata[0][0];
			CRGB* pdata_end = &gamedata[0][0] + sizeof(gamedata)/sizeof(CRGB);
			while (1) {
				int input = Serial.read();
				if (input == '\n' || input == '\r') {
					break;
				} else if (pdata <  pdata_end) {
					if (input == ',') {
						if (!done)
							*pdata = CRGB::Black;
						pdata++;
						done = 0;
					} else if (input >= '0' && input <= '3') {
						*pdata = colors[input - '0'];
						done = 1;
					} else if (input != -1) {
						*pdata = CRGB::Black;
						done = 1;
					}
				}
			}
		}
	}
#endif
}
