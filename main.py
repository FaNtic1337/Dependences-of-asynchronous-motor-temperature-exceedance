import matplotlib.pyplot as plt
import numpy as np
from math import e, sqrt


def create_plot(x_value, y_value, figure_name, color, limits=(0, 0), file_name='testfile.png'):
    plt.figure(figure_name)
    plt.plot(x_value, y_value, color=color)

    plt.grid()

    plt.xlabel('Время, сек')
    plt.ylabel('Температура, °С')

    plt.xlim(limits[0], None)
    plt.ylim(limits[1], None)

    plt.savefig(file_name)


class Engine:
    def __init__(self, heat_resistance_class, Pn, kpd, m, n, S1, S2, S3):

        # initialization variables
        self.heat_resistance_class = heat_resistance_class
        self.Pn = Pn * 1000  # KiloVatt to Vatt
        self.kpd = kpd / 100
        self.m = m  # kg
        self.n = n  # revolutions per minute
        self.S1 = S1 * 60  # minutes to seconds
        self.S2 = S2 * 60  # minutes to seconds
        self.eps = S3 / 100

        # constant instances
        self.с = 385  # heat capacity of copper J*kg/°C
        self.T_nom = 40  # Nominal tempurature 40 °C
        self.T_cool = 24  # Cooling temperature 24 °C
        self.T_max = self.define_T_parameters()[0]  # if heat_resistance_class is F --> 150 °C
        self.T_add = self.define_T_parameters()[1]  # if heat_resistance_class is F --> 110 °C
        self.a = self.define_loss_factor()  # if n > 1000 --> 0.7
        self.dT = self.T_nom - self.T_cool  # temperature for S1_mode

        self.duration_s2 = self.S2  # Can be any

        self.s3_loops = 10
        self.loop_time = self.s3_loops * 60  # 10 min

        # time instances
        self.s1_time = self.setup_time('S1')
        self.s2_time = self.setup_time('S2')
        self.s3_time = self.setup_time('S3')

        # nomimal instances
        self.Tn = 0  # for self.s2_mode_plot()

    # Function for T_max and T_add
    def define_T_parameters(self):
        if self.heat_resistance_class == 'A':
            T_add = 65
            T_max = 40 + T_add
        elif self.heat_resistance_class == 'E':
            T_add = 80
            T_max = 40 + T_add
        elif self.heat_resistance_class == 'B':
            T_add = 90
            T_max = 40 + T_add
        elif self.heat_resistance_class == 'F':
            T_add = 110
            T_max = 40 + T_add
        elif self.heat_resistance_class == 'H':
            T_add = 135
            T_max = 40 + T_add
        else:
            T_add = 0
            T_max = 0
            print('Incorrect input! Please input the right heat resistance class value')

        return [T_max, T_add]

    # Function for a_coefficient
    def define_loss_factor(self):
        if self.n < 1000:
            a = 0.5
        else:
            a = 0.7

        return a

    # Function for time arrays
    def setup_time(self, mode):
        if mode == 'S1':
            time = np.arange(0, self.S1)
        elif mode == 'S2':
            time = np.arange(0, self.S2 * 4)
        elif mode == 'S3':
            time = np.arange(0, self.loop_time * self.s3_loops * 10)
        else:
            time = 0
            print('Incorrect input! Please input the right time value')

        return time

    def s1_nominal_mode_plot(self):

        # Computing formulas
        P_Tn = self.Pn * (1 - self.kpd) / self.kpd
        A = P_Tn / self.T_add
        self.Tn = self.с * self.m / A
        T_state = P_Tn / A

        # Creating T array
        T = []
        for time in self.s1_time:
            T.append(T_state * (1 - e ** (-time / self.Tn)) + self.T_nom)

        # Creating plot
        fig_name = 'Продолжительный режим работы S1 при стандартной температуре 40°С'
        file_name = 's1_nominal.png'

        create_plot(self.s1_time, T, fig_name, 'orange', (0, self.T_nom), file_name)

    def s1_mode_plot(self):

        # Computing formulas
        P_s1 = self.Pn * sqrt(1 + (self.dT * (1 + self.a) / self.T_add))
        P_Ts1 = P_s1 * (1 - self.kpd) / self.kpd
        A = P_Ts1 / self.T_add
        Tn_s1 = self.с * self.m / A
        T_state_s1 = P_Ts1 / A

        # Creating T array
        T = []
        for time in self.s1_time:
            T.append(T_state_s1 * (1 - e ** (-time / Tn_s1)) + self.T_cool)

        # Creating plot
        fig_name = 'Продолжительный режим работы S1 при температуре охлаждающей среды 24°С'
        file_name = 's1_cooling.png'

        create_plot(self.s1_time, T, fig_name, 'blue', (0, self.T_cool), file_name)

    def s2_mode_plot(self):

        # Computing formulas
        P_s2 = self.Pn * sqrt((1 + self.a) / (1 - e ** (-self.duration_s2 / self.Tn)) - self.a)
        P_Ts2 = P_s2 * (1 - self.kpd) / self.kpd
        A = P_Ts2 / self.T_add
        Tn_s2 = self.с * self.m / A
        T_state_s2 = P_Ts2 / A

        # Creating T_on array
        T_on = []
        for time in self.s2_time[:self.duration_s2]:
            T_on.append(T_state_s2 * (1 - e ** (-time / Tn_s2)) + self.T_nom)

        # Creating T_off array
        T_off = []
        for time in self.s2_time:
            T_off.append(T_state_s2 * e ** (-time / Tn_s2) + self.T_nom)

        # Masking T_off to get correct function
        T_off = np.array(T_off)
        T_off_masked = np.ma.masked_where(T_off > T_on[-1], T_off)
        # Crating new T_off without masked instances
        new_T_off = []
        for i in T_off_masked:
            if i != '--':
                new_T_off.append(i)

        # Creating T array
        T = []
        T.extend(T_on)
        T.extend(new_T_off)

        # Creating plot
        fig_name = 'Кратковременный режим работы S2'
        file_name = 's2.png'

        create_plot(self.s2_time, T[:len(self.s2_time)], fig_name, 'red', (0, self.T_nom), file_name)

    def s3_mode_plot(self):

        # Computing formulas
        P_s3 = self.Pn / sqrt(self.eps / (self.eps + (1 + self.a) * (1 - self.eps)))
        P_Ts3 = P_s3 * (1 - self.kpd) / self.kpd
        A = P_Ts3 / self.T_add
        Tn_s3 = self.с * self.m / A
        T_state_s3 = P_Ts3 / A

        # Duration each of periods
        on_time = int(self.eps * self.loop_time)
        off_time = int(self.loop_time - on_time)

        # Crating T_on original array
        T_on = []
        for time in self.s3_time:
            T_on.append(T_state_s3 * (1 - e ** (-time / Tn_s3)) + self.T_nom)

        # Crating T_off original array
        T_off = []
        for time in self.s3_time:
            T_off.append(T_state_s3 * e ** (-time / Tn_s3) + self.T_nom)

        # For first loop (until engine is not turned off)
        new_T_off = [0]

        # Crating T array
        T = []
        for i in range(self.s3_loops):
            # Masking T_on to get correct function
            T_on = np.array(T_on)
            T_on_masked = np.ma.masked_where(T_on < new_T_off[-1], T_on)
            # Crating new T_on without masked instances
            new_T_on = []
            for item in T_on_masked:
                if item != '--' and len(new_T_on) <= on_time:
                    new_T_on.append(item)
                else:
                    if len(new_T_on) > on_time:
                        break
                    else:
                        continue

            # Masking T_off to get correct function
            T_off = np.array(T_off)
            T_off_masked = np.ma.masked_where(T_off > new_T_on[-1], T_off)
            # Crating new T_off without masked instances
            new_T_off = []
            for item in T_off_masked:
                if item != '--' and len(new_T_off) <= off_time:
                    new_T_off.append(item)
                else:
                    if len(new_T_off) > off_time:
                        break
                    else:
                        continue

            T.extend(new_T_on)
            T.extend(new_T_off)

        # Creating plot
        fig_name = 'Периодический повторно-кратковременный режим работы S3'
        file_name = 's3.png'

        create_plot(self.s3_time[:len(T)], T, fig_name, 'green', (0, self.T_nom), file_name)

    def engine_thermal_calculation(self):
        self.s1_nominal_mode_plot()
        self.s1_mode_plot()
        self.s2_mode_plot()
        self.s3_mode_plot()
        plt.show()


if __name__ == '__main__':
    # LSRPM_280_MK1 = Engine('F', 85, 95.9, 545, 1000, 180, 60, 40)
    # LSRPM_280_MK1.engine_thermal_calculation()
    AIR100S4 = Engine('F', 3, 82, 34, 1500, 180, 60, 40)
    AIR100S4.engine_thermal_calculation()

