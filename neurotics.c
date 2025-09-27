#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"

#define N 600          // number of neurons
int u[N];            // membrane potentials
int u_rest = 0;
int u_th = 20;
int tau = 50;
int time = 0;
int led = 25;
int iter = 50; // number of iterations with spikes to record

int lif_step(int *u, int I, int u_th, int u_rest, int tau) {
    *u = *u + I - (*u / tau);
    if (*u >= u_th) {
        *u = u_rest;
        return 1; // spike
    }
    return 0;
}

int main() {
    int I[N];        // input currents
    int spikes[N];   // spike outputs

    // initialize u
    for (int i = 0; i < N; i++) u[i] = u_rest;

    // initialize LED pin
    gpio_init(led);
    gpio_set_dir(led, GPIO_OUT);

    while (iter > 0) {
        // generate random Poisson input
        for (int i = 0; i < N; i++)
            I[i] = (rand() % 100 < 50) ? 10 : 0;

        int spiked = 0;
        // update neurons
        for (int i = 0; i < N; i++) {
            spikes[i] = lif_step(&u[i], I[i], u_th, u_rest, tau);
            if (spikes[i]) {

                printf("%d,%d,%d\n", time, u[i], spikes[i]); // CSV row
                gpio_put(led, 1);
                sleep_ms(50);
                gpio_put(led, 0);
                spiked = 1;
            }
        }
        if (spiked) iter--;
        time++;
        sleep_ms(100);
    }
    return 0;
}
