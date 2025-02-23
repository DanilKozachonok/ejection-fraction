import streamlit as st
import json
from functions import *


def main(config : dict):
    st.set_page_config(
        page_title="get_VECG",
        page_icon='configs/logo.png',
        layout="wide",
        initial_sidebar_state="expanded",)
    st.title("Получение ВЭКГ")
    uploaded_file = st.sidebar.file_uploader("Выберите файл .edf", type="edf")
    if uploaded_file:
        st.write(f"Выбран файл: {uploaded_file.name}")
        st.markdown('---') 

    n_term_start = st.sidebar.number_input("Номер периода ЭКГ", value=config['n_term_start'], min_value=2)
    button_pressed = st.sidebar.button(":red[Запуск]", key="launch_button",
                                       help="Нажмите, чтобы начать обработку данных", use_container_width=True)
    
    
    st.sidebar.markdown('---') 
    st.sidebar.markdown('### Выбор режимов:')
    plot_projections = st.sidebar.checkbox("Построение проекций ВЭКГ", value=config['plot_projections'])
    plot_3D = st.sidebar.checkbox("Построение 3D ВЭКГ", value=config['plot_3D'])
    show_ECG = st.sidebar.checkbox("Отображение ЭКГ отведений", value=config['show_ECG'])
    show_xyz = st.sidebar.checkbox("Отображение ВЭКГ отведений", value=config['show_xyz'])
    predict_res = st.sidebar.checkbox("Результат СППР (болен/здоров)", value=config['predict_res'])
    count_qrst_angle = st.sidebar.checkbox("Расчет угла QRST", value=config['count_qrst_angle'])
    QRS_loop_area = st.sidebar.checkbox("Расчет площади QRS петли", value=config['QRS_loop_area'])
    T_loop_area = st.sidebar.checkbox("Расчет площади ST-T петли", value=config['T_loop_area'])


    st.sidebar.markdown('---') 
    st.sidebar.markdown('### Настройки:')
    mean_filter = st.sidebar.checkbox("Сглаживание петель", value=config['mean_filter'])
    filt = st.sidebar.checkbox("ФВЧ фильтрация ЭКГ сигналов", value=config['filt'])
    if filt:
        f_sreza = st.sidebar.number_input("Частота среза ФВЧ фильтра (в Гц)", value=config['f_sreza'], min_value=0.0)
    f_sampling = st.sidebar.number_input("Частота дискретизации (в Гц)", value=config['f_sampling'],  min_value=1)
    pr_delta = st.sidebar.number_input("Сдвиг от R пика (в долях от размера кардиоцикла)",
                                       value=config['pr_delta'], min_value=0.00, max_value=1.0)
    # Показать только при dev_mode логи обработки
    if config["dev_mode"]:
        logs = st.sidebar.checkbox("Показ логов обработки", value=config['logs'])  # Показать только при dev_mode
    else:
        logs = False


    st.sidebar.markdown('---') 
    

    if button_pressed:
        if uploaded_file is not None:
            temp_file_path = "temp.edf"  # Имя временного файла
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(uploaded_file.read())
            #st.write(f'Загружен файл - {temp_file_path}')

            input_data = {
                "data_edf": temp_file_path,
                "n_term_start": n_term_start,
                "filt": filt,
                "f_sreza": f_sreza if filt else None,
                "f_sampling": f_sampling,
                "plot_projections": plot_projections,
                "plot_3d": plot_3D,
                "show_ecg": show_ECG,
                "predict": predict_res,
                "count_qrst_angle": count_qrst_angle,
                "qrs_loop_area": QRS_loop_area,
                "t_loop_area": T_loop_area,
                "mean_filter": mean_filter,
                "logs": logs,
                "n_term_finish": None,
                "pr_delta": pr_delta,
                "show_xyz": show_xyz,
                "save_coord": False
            }

            # Получить ВЭКГ (запуск гланой функции)
            try:
                output = get_VECG(input_data)
                # Выделение текстовых ответов и plotly графиков
                res = output['text']
                charts = output['charts']
            except ValueError as e:
                # Обработка ошибок
                st.error("Для данного выбранного периода площади не могут быть посчитаны.")
                st.warning("Измените значение номера периода или отключите режим вычисления площадей.")
                if config["dev_mode"]:
                    st.write(f"Код ошибки: {e}")
                res = ()
                charts = []
                
            # Очиста временных файлов после инференса
            os.remove(temp_file_path)
            #st.write(f'Удален файл - {temp_file_path}')

            # Обработаем результаты программы, поместив в список предложения:
            message = []
            error = False
            if res == 'no_this_period':
                st.error("Не найден такой период. Попробуйте ввести меньше значение")
                error = True
            elif res == 'too_noisy':
                st.error("Не получилось построить ВЭКГ, так как ЭКГ слишком шумный")
                error = True
            elif len(res) == 4:
                area_projections, angle_qrst, angle_qrst_front, message_predict = res
                if input_data["predict"]:
                    message.append('__СППР: ' + message_predict)
                if input_data["qrs_loop_area"]:
                    message.append(f'Площадь петли QRS во фронтальной плоскости: {"{:.3e}".format(area_projections[0])}')
                    message.append(f'Площадь петли QRS во сагиттальной плоскости: {"{:.3e}".format(area_projections[1])}')
                    message.append(f'Площадь петли QRS во аксиальной плоскости: {"{:.3e}".format(area_projections[2])}')
                if input_data["qrs_loop_area"] and input_data["t_loop_area"]:
                    message.append(f'Площадь петли ST-T во фронтальной плоскости: {"{:.3e}".format(area_projections[3])}')
                    message.append(f'Площадь петли ST-T во сагиттальной плоскости: {"{:.3e}".format(area_projections[4])}')
                    message.append(f'Площадь петли ST-T во аксиальной плоскости: {"{:.3e}".format(area_projections[5])}')
                elif input_data["t_loop_area"]:
                    message.append(f'Площадь петли ST-T во фронтальной плоскости: {"{:.3e}".format(area_projections[0])}')
                    message.append(f'Площадь петли ST-T во сагиттальной плоскости: {"{:.3e}".format(area_projections[1])}')
                    message.append(f'Площадь петли ST-T во аксиальной плоскости: {"{:.3e}".format(area_projections[2])}')
                if input_data["count_qrst_angle"]:
                    message.append(f'Пространственный угол QRST равен {round(angle_qrst, 2)} градусов')

            # Проверка на факт наличия дополнительных ошибок (для разработчика)
            if isinstance(res, str) and config["dev_mode"] and res not in ['no_this_period', 'too_noisy']: 
                st.error(res)

            # Вывести результаты
            if not error:
                if message != []:
                    for text in message:
                        if 'Здоров' in text: 
                            st.markdown(f'#### :green[{text}]')
                        elif 'Болен' in text:
                            st.markdown(f'#### :red[{text}]')
                        else:
                            st.markdown(f'##### {text}')
            if charts != []:
                for chart in charts:
                    st.plotly_chart(chart, use_container_width=True)

        else:
            st.warning("Пожалуйста, загрузите файл .edf для обработки.")


if __name__ == "__main__":
    # Загрузка конфигурации программы:
    with open('configs/config.json', 'r', encoding='utf-8') as json_file:
        config = json.load(json_file)
    main(config)

