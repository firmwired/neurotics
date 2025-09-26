#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"

int lif_step(int *u, int I, int u_th, int u_rest, int tau) {
    *u = *u + I - (*u / tau);
    if (*u >= u_th) {
        *u = u_rest;
        return 1; // spike
    }
    return 0;
}

int main() {
    stdio_init_all();
    int u_th = 20, u_rest = 0, u = u_rest, tau = 50;
    int led = 25;
    gpio_init(led);
    gpio_set_dir(led, GPIO_OUT);

    int t = 0;
    printf("time,u,spike\n"); // CSV header

    while (true) {
        int I = (rand() % 100 < 50) ? 10 : 0; // Poisson input
        int spike = lif_step(&u, I, u_th, u_rest, tau);

        if (spike) {
            gpio_put(led, 1);
            sleep_ms(50);
            gpio_put(led, 0);
        }

        printf("%d,%d,%d\n", t, u, spike); // CSV row
        t++;
        sleep_ms(100);
    }
}
