# Использование разных голосов для разных персонажей

Во-первых, если в текущем тексте нет указаний на имя персонажа, можно дополнительно выбрать текст с именем в селекторе текста. Отображаемый текст будет упорядочен в соответствии с последовательностью выбора.

Затем в настройках игры -> `Голос` (или в `Настройках голоса` в интерфейсе настроек, но это будет глобальная настройка, что не рекомендуется) отключите опцию `Следовать по умолчанию`, активируйте `Назначение голоса`, добавьте строку в настройки, установите `Условие` как `Содержит`, введите имя персонажа в поле `Цель`, а затем выберите голос в `Назначить как`.

![img](https://image.lunatranslator.org/zh/tts/1.png) 

Однако, из-за дополнительного выбора текста с именем, отображаемый и переводимый контент будет включать имя персонажа, и голос также будет его озвучивать. Чтобы решить эту проблему, активируйте `Коррекцию голоса` и используйте регулярные выражения для фильтрации имени персонажа и связанных символов.

## Подробное объяснение назначения голоса

Когда текущий текст соответствует условиям, выполняется действие, указанное в `Назначить как`.

#### Условия

1. Регулярное выражение
    Определяет, используется ли регулярное выражение для проверки.
1. Условие
    **Начало/конец** Когда выбрано "начало/конец", условие считается выполненным только если цель находится в начале или конце текста.
    **Содержит** Условие считается выполненным, если цель встречается в тексте. Это более мягкое условие.
    При одновременной активации `Регулярное выражение`, система автоматически обработает регулярное выражение для совместимости с этой опцией.
1. Цель
    Текст для проверки, обычно **имя персонажа**.
    При активации `Регулярное выражение`, содержимое будет интерпретироваться как регулярное выражение для более точной проверки.

#### Назначить как

1. Пропустить
    При соответствии условиям пропускать чтение текущего текста

1. По умолчанию
    Для соответствующего содержимого используется чтение голосом по умолчанию. Обычно при очень мягких условиях оценки возможны ложные срабатывания. Чтобы избежать этого, переместите условие действия перед более мягкими критериями.
1. Выбор голоса
    После выбора появится окно для выбора голосового движка и голоса. При соответствии условиям будет использоваться выбранный голос для чтения.
