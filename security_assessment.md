# Smart City IoT — Отчёт по оценке киберрисков

**Проект:** Smart-City-IoT-Monitoring  
**Ветка:** `security-risk-assessment`  
**Тип работы:** защитный анализ (threat modeling + illustrative risk scoring)  
**Дата подготовки отчёта:** 2026-11-09  

> **Важно:** пентест, динамическая эксплуатация уязвимостей и изменение боевой конфигурации брокера **не выполнялись**.  
> Выводы основаны на **статическом обзоре** исходного кода и конфигурации MQTT-системы, а также на учебной модели угроз.

---

## 1. System Overview

Система — учебный IoT-контур мониторинга окружающей среды для районов Еревана. Виртуальные сенсоры генерируют показания температуры, влажности и качества воздуха, передают их через MQTT (Mosquitto), сохраняют в SQLite и отображают в Streamlit-дашборде.

Цель данного отчёта — выполнить **Assignment №13**: построить Threat Model, оценить риски по формуле Probability × Impact и предложить меры защиты, подходящие именно этой архитектуре.

Компоненты исходной MQTT-ветки (`master`):

| Компонент | Путь / артефакт |
|---|---|
| Симулятор сенсоров | `simulator/sensor_simulator.py` |
| MQTT publisher | `simulator/mqtt_publisher.py`, `simulator/run_publisher.py` |
| MQTT broker | `tools/mosquitto/` + `tools/mosquitto/mosquitto.conf` |
| MQTT subscriber | `subscriber/mqtt_subscriber.py`, `subscriber/run_subscriber.py` |
| Валидация сообщений | `subscriber/message_validator.py` |
| SQLite | `database/db.py`, файл `data/smartcity.db` |
| Мониторинг UI | `dashboard/app.py` |
| Зависимости | `requirements.txt` (`paho-mqtt`, `streamlit`, `pandas`, `plotly`) |

Дополнительно на ветке `security-risk-assessment` добавлены модули анализа:

- `security/threats.py` — Threat Model  
- `security/risk_calculator.py` — расчёт рисков  
- `security/recommendations.py` — рекомендации  
- `security_dashboard.py` — отдельный security UI  
- `tests/` — unit-тесты расчётов и маппинга рекомендаций  

---

## 2. Architecture

Фактический поток данных:

```text
Sensor Simulator
       |
       v
MQTT Publisher  --->  Mosquitto Broker (:1883, topic smartcity/sensors)
                              |
                              v
                       MQTT Subscriber + message_validator
                              |
                              v
                       SQLite (data/smartcity.db)
                              |
                              v
                       Streamlit Monitoring Dashboard (:8501)
```

Кратко по движению данных:

1. `SensorSimulator` формирует JSON-показания для четырёх районов.  
2. `MqttPublisher` публикует их в topic `smartcity/sensors` с QoS 0.  
3. Локальный Mosquitto принимает сообщения на порту `1883`.  
4. `MqttSubscriber` парсит JSON, валидирует схему и передаёт валидные записи в БД.  
5. `SensorDatabase` сохраняет строки в таблицу `sensor_readings`.  
6. `dashboard/app.py` читает БД и показывает метрики/графики.

Отдельный `security_dashboard.py` **не участвует** в потоке телеметрии: он только визуализирует модель угроз и риски.

---

## 3. Scope and Assumptions

### В scope

- Статический разбор MQTT-архитектуры на ветке, созданной от `master`.  
- Идентификация активов, точек входа и границ доверия.  
- Учебная Threat Model (минимум 10 угроз).  
- Illustrative risk scoring (P×I) и классификация Low/Medium/High.  
- Рекомендации по защитным мерам.  
- Отчётность и интерактивный security dashboard.

### Вне scope

- Реальные атаки, эксплойты, brute-force, DoS-нагрузка на живой брокер.  
- Автоматическое изменение `mosquitto.conf`, ACL, TLS, firewall.  
- Полный аудит ОС, контейнеров, облачной инфраструктуры.  
- Анализ веток `kafka-pipeline` и `digital-twin` как основных объектов оценки.

### Допущения

1. Рассматривается учебный/демо-контур Smart City, а не промышленный production.  
2. Значения Probability/Impact — **иллюстративные оценки**, согласованные с подтверждёнными находками, а не результаты измерений.  
3. Если порт доступен только на loopback, часть удалённых сценариев менее вероятна; это **не проверялось динамически** на уровне ОС.  
4. Физические IoT-устройства в репозитории отсутствуют: угроза компрометации сенсора моделируется как учебный аналог.

### Легенда доказательности

| Метка | Смысл |
|---|---|
| **Confirmed finding** | Наблюдается в коде или конфигурации |
| **Potential weakness** | Логически следует из confirmed finding, но без эксплуатации |
| **Hypothetical scenario** | Учебный сценарий атаки для модели угроз |
| **Proposed improvement** | Рекомендация; **не утверждается**, что уже внедрена |

---

## 4. Protected Assets

| ID | Актив | Почему важен |
|---|---|---|
| A-01 | Целостность телеметрии сенсоров | Решения/визуализация зависят от достоверности показаний |
| A-02 | Доступность MQTT-брокера | Без брокера поток данных останавливается |
| A-03 | Файл SQLite `data/smartcity.db` | История наблюдений; конфиденциальность + целостность + доступность |
| A-04 | Streamlit monitoring dashboard | Канал чтения оперативных и исторических данных |
| A-05 | Доверие к источнику «сенсорных» данных | Без аутентичности publisher данные нельзя считать измерениями |

---

## 5. Trust Boundaries

| ID | Граница | Что меняется |
|---|---|---|
| B-01 | Сеть/клиенты ↔ Mosquitto | Сейчас для доступа достаточно сетевой достижимости порта (`allow_anonymous true` — **confirmed**) |
| B-02 | MQTT publish ↔ Subscriber validation | Схема/типы проверяются, личность publisher — нет |
| B-03 | Процесс приложения ↔ файл SQLite | Защита в основном на уровне прав ОС (**не верифицировано динамически**) |
| B-04 | Браузер ↔ Streamlit UI | Прикладной аутентификации в `dashboard/app.py` не найдено (**confirmed absence**) |

Точки входа: MQTT `:1883`, topic `smartcity/sensors`, файл БД, Streamlit `:8501`, локальные CLI-процессы.

---

## 6. Threat Model

Ниже — каталог угроз из `security/threats.py`.  
Сценарии атак помечены как гипотетические, даже если опираются на confirmed-конфигурацию.

### T-01 — Unauthorized MQTT broker access

- **Компонент:** Mosquitto  
- **Суть:** подключение/publish/subscribe без учётных данных  
- **Confirmed:** `allow_anonymous true` в `tools/mosquitto/mosquitto.conf`  
- **Hypothetical scenario:** клиент, достигший `:1883`, работает с topic без пароля  
- **Последствия:** утечка live-телеметрии, инъекция ложных данных, помехи легитимным клиентам  

### T-02 — Sensor data spoofing

- **Компонент:** topic `smartcity/sensors` → subscriber → SQLite  
- **Суть:** публикация синтаксически валидного, но чужого JSON  
- **Confirmed:** валидатор проверяет поля/типы, но не аутентичность источника  
- **Hypothetical scenario:** после анонимного доступа публикуются «правдоподобные» показания  
- **Последствия:** искажение мониторинга и истории  

### T-03 — MQTT message interception

- **Компонент:** транспорт MQTT  
- **Confirmed absence:** в проектном `mosquitto.conf` нет TLS-listener  
- **Hypothetical scenario:** перехват plaintext на незащищённом сегменте сети  
- **Примечание:** для чисто localhost-демо практическая вероятность ниже  

### T-04 — DDoS against the MQTT broker

- **Компонент:** доступность Mosquitto  
- **Confirmed absence:** в project conf не найдены connection limits  
- **Hypothetical scenario:** массовые анонимные connect/publish  

### T-05 — Unauthorized database access

- **Компонент:** `data/smartcity.db`  
- **Confirmed:** локальный файл без пароля БД; SQL параметризован  
- **Unverified:** фактические Unix-права на файл  
- **Hypothetical scenario:** локальный пользователь/malware читает или копирует БД  

### T-06 — Data theft

- **Компонент:** MQTT + SQLite + Streamlit  
- **Суть:** составной канал утечки  
- **Опирается на:** анонимный MQTT, отсутствие UI auth, файловый доступ к БД  

### T-07 — Ransomware affecting application data

- **Компонент:** хост + файл БД  
- **Confirmed absence:** в репозитории не найдена автоматизация backup/restore  
- **Hypothetical / out-of-band:** шифрование/удаление `smartcity.db` ransomware на хосте  

### T-08 — Unauthorized dashboard access

- **Компонент:** `dashboard/app.py`  
- **Confirmed absence:** нет login/password flow  
- **Hypothetical scenario:** просмотр графиков при доступности `:8501`  

### T-09 — Malicious or malformed sensor messages

- **Компонент:** subscriber/validator  
- **Confirmed control:** невалидный JSON/типы отбрасываются, в БД не пишутся  
- **Остаточный риск:** валидные, но ложные данные относятся к T-02  

### T-10 — IoT device or sensor compromise

- **Компонент:** учебный аналог полевого устройства / publisher identity  
- **Confirmed:** в проекте виртуальный Python-симулятор, не firmware audit  
- **Hypothetical scenario:** компрометация доверенного источника телеметрии  

---

## 7. Risk Assessment Methodology

Учебная формула (не официальный стандарт):

```text
Risk Score = Probability × Impact
```

### Probability

| Значение | Уровень |
|---:|---|
| 1 | Rare |
| 2 | Unlikely |
| 3 | Possible |
| 4 | Likely |
| 5 | Very likely |

### Impact

| Значение | Уровень |
|---:|---|
| 1 | Negligible |
| 2 | Minor |
| 3 | Moderate |
| 4 | Major |
| 5 | Critical |

### Классификация (по умолчанию, конфигурируемо в коде)

| Score | Level |
|---|---|
| 1–7 | Low |
| 8–14 | Medium |
| 15–25 | High |

Реализация: `security/risk_calculator.py`.  
Валидация отклоняет значения вне диапазона 1..5 и некорректные типы.

Все стартовые оценки помечены как `illustrative_estimate`.

---

## 8. Risk Assessment Table

Актуальные стартовые оценки двигателя рисков:

| Threat ID | Threat name | Component | P | I | Score | Level |
|---|---|---|---:|---:|---:|---|
| T-01 | Unauthorized MQTT broker access | Mosquitto broker | 4 | 4 | 16 | High |
| T-02 | Sensor data spoofing | MQTT topic / subscriber / SQLite | 4 | 4 | 16 | High |
| T-03 | MQTT message interception | MQTT transport | 2 | 3 | 6 | Low |
| T-04 | DDoS against the MQTT broker | Broker availability | 2 | 4 | 8 | Medium |
| T-05 | Unauthorized database access | SQLite file | 3 | 3 | 9 | Medium |
| T-06 | Data theft | MQTT + DB + UI | 3 | 4 | 12 | Medium |
| T-07 | Ransomware affecting application data | Host + SQLite | 2 | 5 | 10 | Medium |
| T-08 | Unauthorized dashboard access | Streamlit dashboard | 4 | 3 | 12 | Medium |
| T-09 | Malicious or malformed sensor messages | Subscriber / validator | 3 | 2 | 6 | Low |
| T-10 | IoT device or sensor compromise | Virtual sensor / publisher | 2 | 4 | 8 | Medium |

**Сводка:** всего 10 угроз; High = 2; Medium = 6; Low = 2; максимальный score = 16.

Краткое обоснование крайностей:

- **T-01/T-02 = High**, потому что анонимный MQTT подтверждён, а подмена schema-valid JSON после этого проста.  
- **T-09 = Low**, потому что malformed payload в основном нейтрализуется существующим validator.  
- **T-03 = Low** в контексте localhost-демо, несмотря на отсутствие TLS.

---

## 9. High-Priority Risks

### 9.1 T-01 Unauthorized MQTT broker access (16 — High)

**Confirmed finding:** `allow_anonymous true`.  
**Potential weakness:** любой клиент с доступом к порту может публиковать/подписываться.  
**Почему приоритет:** это корневая слабость, открывающая путь к spoofing, data theft и части DoS-сценариев.

### 9.2 T-02 Sensor data spoofing (16 — High)

**Confirmed finding:** validator проверяет структуру, не идентичность источника.  
**Hypothetical scenario:** публикация валидного JSON от имени `sensor_01` и т.п.  
**Почему приоритет:** удар по целостности данных Smart City (актив A-01/A-05).

### 9.3 Ближайший «второй эшелон» (Medium, но practically important)

- **T-08 (12):** отсутствие auth у dashboard.  
- **T-06 (12):** несколько каналов утечки.  
- **T-07 (10):** высокий impact при потере БД без проверенных бэкапов.

---

## 10. Recommended Security Controls

Ниже — разделение **existing** и **proposed**.  
Proposed-меры **не были автоматически применены** к брокеру или UI.

### 10.1 Existing controls (подтверждены обзором)

| ID | Control | Связанные угрозы | Как помогает |
|---|---|---|---|
| C-EXIST-01 | Default `localhost` у MQTT-клиентов | T-01, T-03, T-04, T-06 | Снижает случайный remote exposure |
| C-EXIST-02 | Schema validation сообщений | T-02, T-09 | Отсекает неполные/нетипизированные payload |
| C-EXIST-03 | Parameterized SQL | T-05, T-09 | Снижает риск SQL injection |
| C-EXIST-04 | `*.db` в `.gitignore` | T-05, T-06 | Снижает утечку БД через Git |
| C-EXIST-05 | Игнорирование invalid MQTT | T-09 | Повышает устойчивость subscriber |

### 10.2 Proposed improvements (рекомендации)

| Приоритет | Control | Главные угрозы | Ожидаемый эффект |
|---|---|---|---|
| P1 | Отключить anonymous MQTT + password/auth | T-01, T-02, T-04, T-06, T-09, T-10 | ↓ Probability несанкционированного доступа |
| P1 | MQTT ACL по client/topic | T-01, T-02, T-06, T-10 | Ограничение publish/subscribe |
| P1 | Auth для Streamlit / reverse proxy | T-08, T-06 | ↓ Probability просмотра UI посторонними |
| P2 | TLS для MQTT | T-03, T-06 | Защита трафика вне доверенного хоста |
| P2 | Firewall / bind / сегментация | T-01, T-03, T-04, T-08 | Сужение attack surface |
| P2 | Connection/rate limits | T-04, T-09 | Сдерживание флуда |
| P2 | Права на `data/smartcity.db` + least privilege | T-05, T-06, T-07 | ↓ Probability локальной кражи/порчи |
| P2 | Offline/immutable backups + recovery drill | T-07, T-05 | ↓ Impact ransomware/потери данных |
| P3 | Semantic validation / anomaly monitoring | T-02, T-09, T-10 | Доп. слой против правдоподобной подмены |
| P3 | Per-device credentials / mTLS (для реального IoT) | T-02, T-10 | Усиление аутентичности устройств |
| P3 | Patch management хоста и зависимостей | T-05, T-06, T-07 | ↓ Probability host compromise |

Соответствие «пример ↔ архитектура» из задания:

- Unauthorized MQTT → auth, ACL, ограничение сетевого доступа  
- Interception → TLS, сегментация, аккуратное управление секретами  
- DDoS → connection limits, filtering, monitoring  
- Database → file permissions, least privilege, backups  
- Ransomware → protected backups, access restrictions, updates, recovery  
- Dashboard → authentication, reverse proxy, ограничение exposure  

---

## 11. Residual Risks and Limitations

### Остаточные риски даже после proposed-мер

1. Ошибки конфигурации ACL/TLS могут оставить обходные пути.  
2. Инсайдер с легитимными credentials всё ещё может искажать данные.  
3. Ransomware/host compromise полностью не устраняется средствами одного IoT-приложения.  
4. Валидация схемы никогда не равна криптографической аутентичности сообщений.  
5. Учебные оценки P/I могут не совпасть с риск-профилем реального города.

### Ограничения метода

- Выполнен **статический review + threat modeling**, не pentest и не red team.  
- Не проверялись динамически: firewall, фактический bind address, права файла БД, устойчивость к нагрузке.  
- Не анализировались глубоко ветки Kafka/Digital Twin.  
- Security dashboard позволяет what-if изменение P/I в session state; это не «новый аудит», пока значения не пересмотрены экспертом.  
- В отчёте нет секретов/паролей: в проекте отдельных credential-файлов для MQTT/UI не обнаружено.

---

## 12. Conclusion

Для учебной Smart City MQTT-системы наиболее критичны **несанкционированный доступ к брокеру** и **подмена сенсорных данных**. Обе угрозы опираются на подтверждённую конфигурацию анонимного MQTT и отсутствие аутентичности publisher.

Сильные стороны текущего кода: валидация сообщений, параметризованный SQL, игнорирование невалидных payload, локальные defaults клиентов.  
Слабые стороны с точки зрения модели угроз: anonymous MQTT, отсутствие TLS в project conf, отсутствие auth у dashboard, отсутствие проверенной backup-процедуры.

Рекомендуемый порядок усиления для демонстрационного контура:

1. MQTT authentication + запрет anonymous + ACL  
2. Ограничение сетевого exposure брокера и UI  
3. Authentication для Streamlit  
4. Backups/recovery для SQLite  
5. TLS и более строгая семантическая валидация — по мере приближения к production-like стенду  

Итог: репозиторий теперь содержит документированную Threat Model, risk engine, рекомендации, interactive security dashboard и данный отчёт — в формате, пригодном для защиты университетского Assignment №13, без проведения разрушающего security-тестирования.

---

## Приложение A. Как воспроизвести артефакты отчёта

```bash
cd /home/lyudmila/Desktop/tt
source .venv/bin/activate

# Unit-тесты risk engine и recommendations
python -m unittest discover -s tests -v

# Security dashboard
streamlit run security_dashboard.py

# Environmental monitoring (исходная система)
# ./start_demo.sh
# или: streamlit run dashboard/app.py
```

## Приложение B. Карта статусов находок

| Тема | Статус |
|---|---|
| `allow_anonymous true` | Confirmed finding |
| Нет TLS в project `mosquitto.conf` | Confirmed absence |
| Нет UI authentication | Confirmed absence |
| Schema validation | Confirmed existing control |
| Parameterized SQL | Confirmed existing control |
| OS firewall / file mode DB | Unverified |
| Конкретные атаки «уже проведены» | **Не утверждается** |
| Proposed MQTT auth/TLS/ACL | Proposed improvement only |
