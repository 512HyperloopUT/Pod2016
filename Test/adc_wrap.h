/*
 * adc_wrap.h
 *
 *  Created on: Jun 20, 2017
 *      Author: benbe
 */

#ifndef ADC_WRAP_H_
#define ADC_WRAP_H_

#include <stdint.h>
#include <stdbool.h>

#include "pin_wrap.h"

void ADCRead(uint32_t base, uint32_t seq_num, bool masked, uint32_t* buffer);
void EnableADC();

#endif /* ADC_WRAP_H_ */