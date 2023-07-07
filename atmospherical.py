
def GetAtmosphericGasesDataMinus57(frecuency, pressure, temperature):
    rp = pressure/1013
    rt = 288/(273 + temperature)

    # Defino la formula de atenuacion en dB/km para f <= 57 Ghz

    return (((7.27 * rt) / (pow(frecuency, 2) + 0.351 * pow(rp, 2) * pow(rt, 2))) + (7.5 / (pow((frecuency - 57), 2) + 2.44 * pow(rp, 2) * pow(rt, 5)))) * pow(frecuency, 2) * pow(rp, 2) * pow(rt, 2) * 1e-3

def GetAtmosphericGasesDataBetween57and63alternative(frecuency, pressure, temperature):
    rp = pressure/1013
    rt = 288/(273 + temperature)

    # Defino la formula de atenuacion en dB/km para 63 <= f <= 350 Ghz

    return (-1.66 * pow(rp, 2) * pow(rt, 8.5) * (frecuency - 57) * (frecuency - 63)) / (1 - (((frecuency - 60) * (frecuency - 63) * 57) / 18) - (((frecuency - 57) * (frecuency - 60) * 63) / 18)) 

def GetAtmosphericGasesDataBetween57and63(frecuency, pressure, temperature):
    rp = pressure/1013
    rt = 288/(273 + temperature)

    # Defino la formula de atenuacion en dB/km para 63 <= f <= 350 Ghz

    return (((frecuency - 60)*(frecuency - 63))/18) - 1.66 * pow(rp, 2) * pow(rt, 8.5) * (frecuency - 57) * (frecuency - 63) + (((frecuency - 57) * (frecuency - 60))/18)

def GetAtmosphericGasesDataBetween63and350(frecuency, pressure, temperature):
    rp = pressure/1013
    rt = 288/(273 + temperature)

    # Defino la formula de atenuacion en dB/km para 63 <= f <= 350 Ghz

    return ((2 * pow(10, -4) * pow(rt, 1.5) * (1 - 1.2 * pow(10, -5) * pow(frecuency, 1.5)))
            + (4 / (pow(( frecuency - 63 ), 2) + 1.5 * pow(rp, 2) * pow(rt, 5))) 
            + (0.28 * pow(rt, 2)) / ( pow(frecuency - 118.75, 2) + 2.84 * pow(rp, 2) * pow(rt, 2)))* pow(frecuency, 2) * pow(rp, 5) * pow(rt, 5) * 1e-3 

def attenuationByWaterVapor(frecuency, pressure, temperature, waterDensity):
    rp = pressure/1013
    rt = 288/(273 + temperature)

    return (( 3.27 * 1e-2 ) * rt + 1.67 * 1e-3 * ((waterDensity * pow(rt, 7))/rp) + 
            7.7 * 1e-4 * pow(frecuency, 0.5) + 
            3.79 / (pow((frecuency - 22.235), 2) + 9.81 * pow(rp, 2) * rt) +
            (((11.73 * rt) / (pow((frecuency - 183.31), 2) + 11.85 * pow(rp, 2) * rt)) +
             ((4.01 * rt) / ((pow((frecuency - 325.153), 2) + 10.44 * pow(rp, 2) * rt))))) * pow(frecuency, 2) * waterDensity * rp * rt * 1e-4