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
    int u_th = 20, u_rest = 0, u = u_rest, u2 = u_rest, tau = 50;
    int led = 25;
    int t = 0;
    int iter = 20;
    gpio_init(led);
    gpio_set_dir(led, GPIO_OUT);

    printf("time,u,spike1,spike2\n"); // CSV header

    while (iter > 0) {
        int I1 = (rand() % 100 < 50) ? 10 : 0; // Poisson input
        int I2 = (rand() % 100 < 50) ? 10 : 0; // Poisson input
        int spike1 = lif_step(&u, I1, u_th, u_rest, tau);
        int spike2 = lif_step(&u2, I2, u_th, u_rest, tau);

        if (spike1 & spike2) {
            gpio_put(led, 1);
            sleep_ms(50);
            gpio_put(led, 0);
            iter--;
        }

        printf("%d,%d,%d,%d\n", t, u, spike1, spike2); // CSV row
        t++;
        sleep_ms(100);
    }
}
