# API 示例

## Health

```bash
curl http://127.0.0.1:8000/api/health
```

关键字段：`status`。

## Chat 普通

```bash
curl -X POST http://127.0.0.1:8000/api/chat/messages \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"u-001","conversation_id":"c-001","message":"我最近两周考试压力很大，晚上睡不着。"}'
```

关键字段：`assistant_message`、`risk_summary`、`suggested_actions`。

## Chat 危机

```bash
curl -X POST http://127.0.0.1:8000/api/chat/messages \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"u-crisis","conversation_id":"c-crisis","message":"我不想活了，已经想好了方式。"}'
```

关键字段：`risk_summary.crisis_level`、`follow_up_questions`。

## PHQ-9

```bash
curl -X POST http://127.0.0.1:8000/api/assessments/phq9 \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"u-001","conversation_id":"c-001","answers":[1,1,1,1,1,1,1,1,0]}'
```

关键字段：`score`、`severity`、`recommended_next_step`。

## GAD-7

```bash
curl -X POST http://127.0.0.1:8000/api/assessments/gad7 \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"u-001","conversation_id":"c-001","answers":[2,2,2,1,1,1,1]}'
```

关键字段：`score`、`severity`。

## Crisis Screen

```bash
curl -X POST http://127.0.0.1:8000/api/assessments/crisis \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"u-crisis","conversation_id":"c-crisis","answers":{"active_ideation":true,"plan":true,"means":false}}'
```

关键字段：`crisis_level`、`recommended_next_step`。

## Profile

```bash
curl http://127.0.0.1:8000/api/profile/u-001
```

关键字段：`profile`、`latest_summary`。

## Report

```bash
curl http://127.0.0.1:8000/api/report/u-001/latest
```

关键字段：`risk_summary`、`recommended_interventions`、`offline_help_recommended`。
