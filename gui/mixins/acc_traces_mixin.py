import numpy as np
import pyqtgraph as pg

from constants import (ADD_TRACE_MODE, MARKER_TRACES, TRACE_HOLD, TRACE_OFF,
                       TRACE_ON)
from gui.styles import Style


class AccTracesMixin:
    """Миксин: накопительные трассы с режимами Off/On/Hold.

    Off — кривая удалена, накопление забыто; On — накапливает
    по кадрам и рисует; Hold — заморожена (не копит), но остаётся
    на экране (аналог View на анализаторе). Переход Hold → On
    сбрасывает накопление: Hold — фиксация результата, не пауза.

    Смена типа накопления (Максимум/Минимум/Средний) сбрасывает
    буфер; если трасса была в Hold — она автоматически переводится
    в On и накопление начинается заново.

    Предполагается, что у окна есть:
    - self.plotWidget (PlotMixin);
    - self.trc_{1,2}_on (комбобокс режима) и self.trc_{1,2}_acc
      (комбобокс типа накопления);
    - PlotMixin.update_state вызывает _update_acc_traces по кадру
      и _reset_acc_traces при смене X-диапазона.
    """

    ACC_TRACE_PEN = {1: Style.ACC_TRACE_COLOR_1, 2: Style.ACC_TRACE_COLOR_2}

    # Запас фильтра адекватности: значения за пределами шкалы экрана
    # более чем на эту величину — артефакт перестройки прибора
    ACC_MARGIN_DB = 50.0
    LEGEND_MARGIN = 6   # отступ легенды от правой кромки графика, px

    def connect_acc_traces(self) -> None:
        """Подключить сигналы режимов и типов накопления.

        Структура накопления создаётся здесь сразу (не лениво): иначе
        hasattr-фильтр в update_state пропустит кадры между постановкой
        режима и первым «касанием» структуры — трасса оживает только
        со второго включения.
        """
        self._acc_entries()
        for num in (1, 2):
            combo_mode = getattr(self, f'trc_{num}_on', None)
            if combo_mode is not None:
                combo_mode.currentTextChanged.connect(
                    lambda _text, n=num: self._acc_mode_changed(n))
            combo_acc = getattr(self, f'trc_{num}_acc', None)
            if combo_acc is not None:
                combo_acc.currentTextChanged.connect(
                    lambda _text, n=num: self._acc_kind_changed(n))

        self._make_acc_legend()

        # Легенда прижимается к углу — следить за изменением геометрии
        vb = self.plotWidget.getPlotItem().getViewBox()
        vb.sigResized.connect(self._place_acc_legend)

    def _acc_entries(self) -> dict:
        """Структура накопления обеих трасс (создаётся один раз)."""
        if not hasattr(self, '_acc_traces'):
            self._acc_traces = {
                num: {'curve': None, 'arr': None, 'count': 0, 'freqs': None,
                      'det': None}
                for num in (1, 2)
            }
        return self._acc_traces

    def _acc_mode(self, num: int) -> str:
        """Текущий режим трассы ('Off'/'On'/'Hold')."""
        combo = getattr(self, f'trc_{num}_on', None)
        return combo.currentText() if combo is not None else TRACE_OFF

    def _acc_clear(self, num: int) -> None:
        """Полностью забыть трассу: удалить кривую, сбросить буфер."""
        entry = self._acc_entries()[num]
        entry['arr'] = None
        entry['count'] = 0
        entry['freqs'] = None
        entry['det'] = None
        if entry['curve'] is not None:
            self.plotWidget.removeItem(entry['curve'])
            entry['curve'] = None

    def _acc_mode_changed(self, num: int) -> None:
        """Реакция на смену РЕЖИМА трассы (Off/On/Hold).

        Сброс буфера при: уходе в Off (с удалением кривой) и при любом
        входе в On — в том числе из Hold (Hold — фиксация результата,
        а не пауза: накопление всегда начинается заново).

        Кривую при сбросе не трогаем: до первого нового кадра она
        просто показывает прежние данные, потом перезаписывается.

        Уход в Off также возвращает все маркеры, стоявшие на этой
        трассе, на основную (trace_idx = 1): трассы больше нет на
        экране — и маркер, и его частота в легенде должны жить на
        существующем источнике данных.
        """
        if self._acc_mode(num) == TRACE_OFF:
            self._acc_clear(num)
            self._markers_to_main_trace(num)
        elif self._acc_mode(num) == TRACE_ON:
            self._acc_reset(num)
        # Hold — ничего делать не нужно: накопление заморожено циклом
        self._update_acc_legend()

    def _markers_to_main_trace(self, num: int) -> None:
        """Вернуть маркеры с выключенной трассы num на основную.

        Вызывается при уходе трассы в Off. Активному маркеру заодно
        синхронизируется комбобокс (setCurrentText штатно триггерит
        _on_mrk_trace_changed — тот обновит легенду маркеров); для
        неактивных достаточно переназначения trace_idx — их легенда
        пересоберётся следом.
        """
        if not hasattr(self, '_marker_entries'):
            return
        moved_any = False
        for entry in self._marker_entries.values():
            if entry['trace_idx'] == num + 1:
                entry['trace_idx'] = 1
                moved_any = True
        if (
            moved_any
            and self._marker_active is not None
            and self._marker_entries[self._marker_active]['trace_idx'] == 1
        ):
            combo = getattr(self, 'combo_mrk_trace', None)
            if combo is not None:
                combo.setCurrentText(MARKER_TRACES[0])
        if hasattr(self, '_update_markers_legend'):
            self._update_markers_legend()

    def _acc_kind_changed(self, num: int) -> None:
        """Реакция на смену ТИПА накопления (Максимум/Минимум/Средний).

        При Hold и Off — автоматический перевод трассы в On: тот, кто
        меняет тип накопления, хочет видеть результат с новым правилом.
        setCurrentText триггерит _acc_mode_changed, который и делает
        сброс буфера. При On — сброс сам: смешивать max/min/aver в
        одном массиве нельзя.
        """
        mode = self._acc_mode(num)
        if mode != TRACE_ON:
            combo_on = getattr(self, f'trc_{num}_on', None)
            if combo_on is not None:
                combo_on.setCurrentText(TRACE_ON)
        else:   # On — буфер сбрасываем, кривую не трогаем
            self._acc_reset(num)
        self._update_acc_legend()

    def _reset_acc_traces(self) -> None:
        """Сбросить накопление при смене частотной сетки.

        Замороженные (Hold) трассы не трогаем: удержанный результат
        должен пережить панорамирование — это и есть смысл Hold.
        Кривые On-трасс остаются отрисованными до первого нового кадра.
        """
        for num, entry in self._acc_entries().items():
            if self._acc_mode(num) == TRACE_HOLD:
                continue
            self._acc_reset(num)

    def _update_acc_traces(self, state) -> None:
        """Обновить накопительные трассы по текущему кадру.

        Фильтр адекватности (как у водопада): кадр, где хотя бы один
        уровень выходит за шкалу экрана с запасом ACC_MARGIN_DB,
        пропускается ЦЕЛИКОМ — один испорченный отсчёт отравил бы
        «Максимум» навсегда.
        """
        if not state.levels:
            return
        levels = np.asarray(state.levels, dtype=np.float64)

        if self._current_reflevel is not None \
                and self._current_range is not None:
            vmin = self._current_reflevel - self._current_range
            vmax = self._current_reflevel
        else:
            vmin = vmax = None

        if vmin is not None:
            eps = 1e-6
            lo_limit = vmin - self.ACC_MARGIN_DB
            hi_limit = vmax + self.ACC_MARGIN_DB
            if (levels.min() < lo_limit - eps) \
                    or (levels.max() > hi_limit + eps):
                return   # кадр-артефакт — не копим, кривую не трогаем

        for num, entry in self._acc_entries().items():
            mode = self._acc_mode(num)
            if mode == TRACE_OFF:
                continue

            combo = getattr(self, f'trc_{num}_acc', None)
            acc_kind = ADD_TRACE_MODE.get(
                combo.currentText()) if combo is not None else None
            if acc_kind is None:
                continue

            if mode == TRACE_ON:
                if entry['arr'] is None or len(entry['arr']) != len(levels):
                    entry['arr'] = levels.copy()
                    entry['count'] = 1
                elif acc_kind == 'max':
                    np.maximum(entry['arr'], levels, out=entry['arr'])
                elif acc_kind == 'min':
                    np.minimum(entry['arr'], levels, out=entry['arr'])
                else:
                    entry['count'] += 1
                    entry['arr'] += (levels - entry['arr']) / entry['count']

                entry['freqs'] = state.freqs   # сетка этого буфера
                # Детектор буфера: во время прогона S/N кэш _main_trace_det
                # уже отражает измерный детектор (quick-опрос после det_set)
                entry['det'] = self._main_trace_det

                if entry['curve'] is None:
                    entry['curve'] = self.plotWidget.plot(
                        [], [],
                        pen=pg.mkPen(self.ACC_TRACE_PEN[num], width=1))
                entry['curve'].setData(state.freqs, entry['arr'])
            # TRACE_HOLD: накопление заморожено — кривую не трогаем,
            # она продолжает показывать последнее накопленное

        self._update_acc_legend()

    def _make_acc_legend(self) -> None:
        """Создать легенду доп. трасс в правом верхнем углу графика.

        Один TextItem на все строки, добавлен прямо в сцену: позиция
        задаётся в пикселях области графика и не зависит от
        панорамирования (как у меток CF/Span в PlotMixin). Якорь не
        используем — его пересчёт не срабатывает после setHtml,
        выравниванием управляет _place_acc_legend.
        """
        self._acc_legend = pg.TextItem(text='', color=Style.PLOT_LABEL_COLOR,
                                       anchor=(0, 0))
        self.plotWidget.scene().addItem(self._acc_legend)
        self._place_acc_legend()

    def _place_acc_legend(self) -> None:
        """Прижать легенду к правому верхнему углу области данных.

        Прямоугольник берётся в координатах сцены (sceneBoundingRect):
        boundingRect() ViewBox отдаёт локальные координаты, где ноль —
        левый верхний угол полотна, а позиция TextItem задана в сценах
        и смещена на ширину осей. Именно отсюда растут «магические»
        +50/+24 у соседних меток — здесь они не нужны.
        """
        if not hasattr(self, '_acc_legend'):
            return
        w = self._acc_legend.textItem.boundingRect().width()
        rect = self.plotWidget.getPlotItem().getViewBox().sceneBoundingRect()
        self._acc_legend.setPos(rect.right() - self.LEGEND_MARGIN - w,
                                rect.top() + 4)

    def _update_acc_legend(self) -> None:
        """Пересобрать текст легенды по включённым трассам.

        Первая строка — режим главного графика: коды накопления и
        детектора из DeviceState в нижнем регистре ('writ, pos').
        Пока данные не приходили, строка не показывается.
        Для накопления 'Blank' (BLAN) строка о главном графике отсутствует
        целиком — трасса скрыта с экрана прибора.

        Каждая строка '<режим накопления>' цветом кривой трассы
        (rich text, цвет в span'ах). У замороженной трассы добавляется
        суффикс '(hold)'. Выключенные (Off) не показываются; если
        выключены обе — остаётся только строка главного графика.
        """
        lines = []

        # --- Строка главного графика ---
        if self._main_visible and self._main_trace_acc != 'BLAN':
            parts = []
            if self._main_trace_det:
                parts.append(self._main_trace_det.lower().capitalize())
            if self._main_trace_acc:
                parts.append(self._main_trace_acc.lower().capitalize())
            if parts:
                lines.append(
                    f'<span style="color:{Style.MAIN_TRACE_COLOR};">'
                    f'{", ".join(parts)}</span>')

        # --- Строки доп. трасс: детектор + накопление, как у главного ---
        for num in (1, 2):
            mode = self._acc_mode(num)
            if mode == TRACE_OFF:
                continue
            combo = getattr(self, f'trc_{num}_acc', None)
            kind = ADD_TRACE_MODE.get(
                combo.currentText(), '?') if combo is not None else '?'
            det = self._acc_entries()[num].get('det') or self._main_trace_det
            parts = []
            if det:
                parts.append(det.lower().capitalize())
            parts.append(kind.capitalize())
            suffix = ' (hold)' if mode == TRACE_HOLD else ''
            lines.append(
                f'<span style="color:{self.ACC_TRACE_PEN[num]};">'
                f'{", ".join(parts)}{suffix}</span>')

        ti = self._acc_legend.textItem
        ti.setHtml('<br>'.join(lines))
        self._place_acc_legend()

    def _load_hold_trace(self, num: int, freqs: list, arr: list) -> None:
        """Загрузить замороженный буфер трассы num (например, из файла).

        Кривая создаётся при необходимости: в отличие от живого цикла
        накопления, загрузка файла может случиться при ещё не созданной
        кривой — сигналы комбобоксов в момент загрузки заглушены.
        """
        entry = self._acc_entries()[num]
        entry['freqs'] = list(freqs)
        entry['arr'] = np.asarray(arr, dtype=np.float64)
        entry['count'] = 0
        if entry['curve'] is None:
            entry['curve'] = self.plotWidget.plot(
                [], [], pen=pg.mkPen(self.ACC_TRACE_PEN[num], width=1))
        entry['curve'].setData(freqs, entry['arr'])

    def _acc_reset(self, num: int) -> None:
        """Сбросить буфер трассы num, не трогая кривую и режим.

        Кривая продолжает показывать прежние данные до первого нового
        кадра — так ведут себя и существующие пути сброса.
        """
        entry = self._acc_entries()[num]
        entry['arr'] = None
        entry['count'] = 0
        entry['freqs'] = None
        entry['det'] = None

    def refresh_acc_trace(self, num: int) -> None:
        """Принудительный сброс накопления трассы num (кнопка «обновить»).

        On — буфер очищается, накопление начинается заново со следующего
        кадра. Hold — трасса автоматически переводится в On: setCurrentText
        триггерит _acc_mode_changed, который и делает сброс (Hold —
        фиксация результата, не пауза). Off — ничего не делает.
        """
        mode = self._acc_mode(num)
        if mode == TRACE_OFF:
            return
        # «освежить» имеет смысл только на живом экране
        self._ensure_unpaused()
        if mode == TRACE_HOLD:
            combo = getattr(self, f'trc_{num}_on', None)
            if combo is not None:
                # сигнальный путь: сброс внутри
                combo.setCurrentText(TRACE_ON)
        else:
            self._acc_reset(num)
