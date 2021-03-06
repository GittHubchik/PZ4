import numpy
import tools
import numpy.fft as fft
#import matplotlib.pyplot as plt
import pylab

class Ricker:
    '''
    Источник, создающий импульс в форме вейвлета Рикера
    '''

    def __init__(self, Np, Md, eps=1.0, mu=1.0, Sc=1.0, magnitude=1.0):
        '''
        magnitude - максимальное значение в источнике;
        Nl - количество отсчетов на длину волны;
        Md - определяет задержку импульса;
        Sc - число Куранта;
        magnitude - максимальное значение в источнике.
        '''
        self.Np = Np
        self.Md = Md
        self.eps = eps
        self.mu = mu
        self.Sc = Sc
        self.magnitude = magnitude

    def getField(self, m, q):
        t = (numpy.pi ** 2) * (self.Sc *
            (q - m * numpy.sqrt(self.eps * self.mu)) / self.Np - self.Md) ** 2
        return self.magnitude * (1 - 2 * t) * numpy.exp(-t)

if __name__ == '__main__':
    # Волновое сопротивление свободного пространства
    W0 = 120.0 * numpy.pi

    # Число Куранта
    Sc = 1.0

    #Скорость света
    c = 3e8

    # Время расчета в отсчетах
    maxTime = 1700

    #Размер области моделирования в метрах
    X = 3.0

    #Размер ячейки разбиения
    dx = 5e-3

    # Размер области моделирования в отсчетах
    maxSize = int(X / dx)

    #Шаг дискретизации по времени
    dt = Sc * dx / c

    # Положение источника в отсчетах
    sourcePos = 100

    # Датчики для регистрации поля
    probesPos = [50,150]
    probes = [tools.Probe(pos, maxTime) for pos in probesPos]

    #1й слой диэлектрика
    eps1 = 5.5
    d1 = 0.3
    layer_1 = int(maxSize / 2) + int(d1 / dx)

    #2й слой диэлектрика
    eps2 = 2.3
    d2 = 0.2
    layer_2 = layer_1 + int(d2 / dx)

    #3й слой диэлектрика
    eps3 = 1.0

    # Параметры среды
    # Диэлектрическая проницаемость
    eps = numpy.ones(maxSize)
    eps[int(maxSize/2):layer_1] = eps1
    eps[layer_1:layer_2] = eps2
    eps[layer_2:] = eps3
    
    # Магнитная проницаемость
    mu = numpy.ones(maxSize - 1)

    Ez = numpy.zeros(maxSize)
    Hy = numpy.zeros(maxSize - 1)

    source = Ricker(30.0, 1.5, eps[sourcePos], mu[sourcePos])


    # Параметры отображения поля E
    display_field = Ez
    display_ylabel = 'Ez, В/м'
    display_ymin = -1.1
    display_ymax = 1.1

    # Создание экземпляра класса для отображения
    # распределения поля в пространстве
    display = tools.AnimateFieldDisplay(maxSize,
                                        display_ymin, display_ymax,
                                        display_ylabel,dx)

    display.activate()
    display.drawProbes(probesPos)
    display.drawSources([sourcePos])
    display.drawBoundary(int(maxSize / 2))
    display.drawBoundary(layer_1)
    display.drawBoundary(layer_2)

    for q in range(maxTime):
        # Расчет компоненты поля H
        Hy = Hy + (Ez[1:] - Ez[:-1]) * Sc / (W0 * mu)

        # Источник возбуждения с использованием метода
        # Total Field / Scattered Field
        Hy[sourcePos - 1] -= Sc / (W0 * mu[sourcePos - 1]) * source.getField(0, q)

        # Граничные условия для поля E
        Ez[0] = Ez[1]
        Ez[-1] = Ez[-2]
        
        # Расчет компоненты поля E
        Hy_shift = Hy[:-1]
        Ez[1:-1] = Ez[1:-1] + (Hy[1:] - Hy_shift) * Sc * W0 / eps[1:-1]

        # Источник возбуждения с использованием метода
        # Total Field / Scattered Field
        Ez[sourcePos] += (Sc / (numpy.sqrt(eps[sourcePos] * mu[sourcePos])) *
                          source.getField(-0.5, q + 0.5))

        # Регистрация поля в датчиках
        for probe in probes:
            probe.addData(Ez, Hy)

        if q % 5 == 0:
            display.updateData(display_field, q)

    display.stop()
    

    # Отображение сигнала, сохраненного в датчиках
    tools.showProbeSignals(probes, -1.1, 1.1, dt)

    # Построение падающего и отраженного спектров и
    # зависимости коэффициента отражения от частоты
    
    # Максимальная и минимальная частоты для отображения коэф-та отражения
    Fmin = 0.2e9
    Fmax = 2e9
    
    size = 2 ** 18
    df = 1 / (size * dt)
    f = numpy.arange(-size / 2 * df, size / 2 * df, df)
    
    # Расчет спектра падающего поля
    fall = numpy.zeros(maxTime)
    fall[:200] = probes[1].E[:200]
    fall_spectr = numpy.abs(fft.fft(fall, size))
    fall_spectr = fft.fftshift(fall_spectr)

    # Расчет спектра отраженного поля
    scattered_spectr = numpy.abs(fft.fft(probes[0].E, size))
    scattered_spectr = fft.fftshift(scattered_spectr)

    # Построение графиков
    fig, ax = pylab.subplots()
    ax.plot(f * 1e-9, fall_spectr / numpy.max(fall_spectr))
    ax.plot(f * 1e-9, scattered_spectr / numpy.max(fall_spectr))
    ax.grid()
    ax.set_xlim(0, 6e9 * 1e-9)
    ax.set_xlabel('f, ГГц')
    ax.set_ylabel('|P / Pmax|')
    ax.legend(['Спектр падающего сигнала','Спектр отраженного сигнала'])
    pylab.show()

    fig, ax = pylab.subplots()
    ax.plot(f * 1e-9, scattered_spectr / fall_spectr)
    ax.grid()
    ax.set_xlim(Fmin * 1e-9, Fmax * 1e-9)
    ax.set_ylim(0, 1)
    ax.set_xlabel('f, ГГц')
    ax.set_ylabel('|Г|')
    pylab.show()
    
