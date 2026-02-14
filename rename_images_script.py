import os

# Mapping of Old URL -> New URL
rename_map = {
    "./picture/idem_ts_study_017_第17章止め方②_ロック原子的操作atomicで同時を捌く.png": "./picture/idem_ts_study_017_ch17_stopping_2_handling_concurrency_with_atomic_lock.png",
    "./picture/idem_ts_study_017_174_ロックとatomicのざっくり定義.png": "./picture/idem_ts_study_017_174_lock_and_atomic_rough_definition.png",
    "./picture/idem_ts_study_017_状態遷移王道パターン.png": "./picture/idem_ts_study_017_state_transition_golden_pattern.png",
    "./picture/idem_ts_study_017_③_複数台でも守りたいdbのatomic更新_or_redisロック.png": "./picture/idem_ts_study_017_3_atomic_db_update_or_redis_lock_for_multiple_servers.png",
    "./picture/idem_ts_study_017_ざっくり処理フロー擬似.png": "./picture/idem_ts_study_017_rough_process_flow_pseudo.png",
    "./picture/idem_ts_study_017_方式b行ロックselect__for_updateで読んだ瞬間にロック.png": "./picture/idem_ts_study_017_method_b_row_lock_select_for_update.png",
    "./picture/idem_ts_study_017_1712_ai活用この章で効く使い方.png": "./picture/idem_ts_study_017_1712_ai_usage_tips_for_this_chapter.png",
    "./picture/idem_ts_study_018_第18章失敗はどう扱うリトライokngの分類.png": "./picture/idem_ts_study_018_ch18_handling_failures_retry_ok_ng_classification.png",
    "./picture/idem_ts_study_018_②_恒久的な失敗リトライng.png": "./picture/idem_ts_study_018_2_permanent_failure_retry_ng.png",
    "./picture/idem_ts_study_018_ルール3回数上限は必須無限リトライしない.png": "./picture/idem_ts_study_018_rule3_retry_limit_essential_no_infinite_retry.png",
    "./picture/idem_ts_study_018_183_まずは_分類表_を持とう.png": "./picture/idem_ts_study_018_183_first_have_classification_table.png",
    "./picture/idem_ts_study_018_185_typescriptミニ実装安全寄りリトライ_retryfetch.png": "./picture/idem_ts_study_018_185_typescript_mini_implementation_safe_retry_fetch.png",
    "./picture/idem_ts_study_018_演習1エラー分類表を作ろう.png": "./picture/idem_ts_study_018_exercise1_create_error_classification_table.png",
    "./picture/idem_ts_study_018_プロンプト2自分のapi仕様に当てはめ.png": "./picture/idem_ts_study_018_prompt2_apply_to_own_api_spec.png",
    "./picture/idem_ts_study_019_第19章失敗結果も保存する冪等__エラー保存戦略.png": "./picture/idem_ts_study_019_ch19_idempotency_saving_failure_results_error_storage_strategy.png",
    "./picture/idem_ts_study_019_2_失敗結果を保存するメリット.png": "./picture/idem_ts_study_019_2_benefits_of_saving_failure_results.png",
    "./picture/idem_ts_study_019_3_失敗結果を保存しないメリット.png": "./picture/idem_ts_study_019_3_benefits_of_not_saving_failure_results.png",
    "./picture/idem_ts_study_019_5_ざっくり早見表ミニ注文api想定.png": "./picture/idem_ts_study_019_5_rough_reference_table_mini_order_api.png",
    "./picture/idem_ts_study_019_7_ミニ注文apiエラー保存つき_冪等ストア_実装方針a.png": "./picture/idem_ts_study_019_7_mini_order_api_with_error_storage_idempotency_store_impl_plan_a.png",
    "./picture/idem_ts_study_019_8_方針aの注意点ここだけは押さえてね.png": "./picture/idem_ts_study_019_8_plan_a_key_points_to_remember.png",
    "./picture/idem_ts_study_019_10_ai活用判断力を爆上げするプロンプト集.png": "./picture/idem_ts_study_019_10_ai_usage_prompts_to_boost_judgment.png",
    "./picture/idem_ts_study_020_第20章httpレスポンス設計200201202409など.png": "./picture/idem_ts_study_020_ch20_http_response_design_200_201_202_409_etc.png",
    "./picture/idem_ts_study_020_2_冪等性とレスポンス設計がぶつかるポイント.png": "./picture/idem_ts_study_020_2_idempotency_and_response_design_conflicts.png",
    "./picture/idem_ts_study_020_失敗系クライアント原因.png": "./picture/idem_ts_study_020_failure_client_causes.png",
    "./picture/idem_ts_study_020_5_ミニ注文apiレスポンス設計の完成形サンプル.png": "./picture/idem_ts_study_020_5_mini_order_api_response_design_complete_sample.png",
    "./picture/idem_ts_study_020_例1同じidempotencykeyなのに本文が違う.png": "./picture/idem_ts_study_020_ex1_same_idempotency_key_different_body.png",
    "./picture/idem_ts_study_020_409冪等キー衝突を返す例.png": "./picture/idem_ts_study_020_409_returning_idempotency_key_conflict_example.png",
    "./picture/idem_ts_study_020_9_ai活用プロンプトコピペok.png": "./picture/idem_ts_study_020_9_ai_usage_prompt_copy_paste_ok.png",
    "./picture/idem_ts_study_021_第21章非同期の世界は重複配送が普通キュー入門.png": "./picture/idem_ts_study_021_ch21_async_world_duplicate_delivery_is_normal_queue_intro.png",
    "./picture/idem_ts_study_021_213_少なくとも1回配送atleastonceって.png": "./picture/idem_ts_study_021_213_at_least_once_delivery.png",
    "./picture/idem_ts_study_021_パターンb可視性タイムアウトvisibility_timeout切れ.png": "./picture/idem_ts_study_021_pattern_b_visibility_timeout_expired.png",
    "./picture/idem_ts_study_021_217_重複配送でも壊れない処理の条件.png": "./picture/idem_ts_study_021_217_conditions_for_process_safe_against_duplicate_delivery.png",
    "./picture/idem_ts_study_021_条件3記録と副作用の順番をミスらない.png": "./picture/idem_ts_study_021_condition3_do_not_mess_up_order_of_recording_and_side_effects.png",
    "./picture/idem_ts_study_021_③_consumer本体重複なら即return.png": "./picture/idem_ts_study_021_3_consumer_body_return_immediately_if_duplicate.png",
    "./picture/idem_ts_study_021_演習1次の処理重複したら何が起きる.png": "./picture/idem_ts_study_021_exercise1_what_happens_if_next_process_duplicates.png",
    "./picture/idem_ts_study_022_第22章outboxと冪等性取りこぼし二重送信を減らす.png": "./picture/idem_ts_study_022_ch22_outbox_and_idempotency_reducing_missed_double_sends.png",
    "./picture/idem_ts_study_022_事故パターンbイベント送信は成功dbがロールバックウソ通知.png": "./picture/idem_ts_study_022_accident_pattern_b_event_sent_db_rollback_false_notification.png",
    "./picture/idem_ts_study_022_図にするとこんな感じ.png": "./picture/idem_ts_study_022_diagram_looks_like_this.png",
    "./picture/idem_ts_study_022_61_sqlorders_と_outbox.png": "./picture/idem_ts_study_022_61_sql_orders_and_outbox.png",
    "./picture/idem_ts_study_022_受け取り側でやること最小.png": "./picture/idem_ts_study_022_receiver_side_minimal_tasks.png",
    "./picture/idem_ts_study_022_落とし穴③payloadが巨大個人情報モリモリ.png": "./picture/idem_ts_study_022_pitfall3_huge_payload_personal_info.png",
    "./picture/idem_ts_study_022_演習2outboxレコードの型定義を作ろう.png": "./picture/idem_ts_study_022_exercise2_create_outbox_record_type_definition.png",
    "./picture/idem_ts_study_023_第23章冪等性テスト2回10回同時実行.png": "./picture/idem_ts_study_023_ch23_idempotency_test_2_times_10_concurrent_executions.png",
    "./picture/idem_ts_study_023_今どきの道具えらびざっくり結論.png": "./picture/idem_ts_study_023_modern_tool_selection_rough_conclusion.png",
    "./picture/idem_ts_study_023_c_エラー時の扱い.png": "./picture/idem_ts_study_023_c_handling_errors.png",
    "./picture/idem_ts_study_023_2_api本体express.png": "./picture/idem_ts_study_023_2_api_body_express.png",
    "./picture/idem_ts_study_023_ここでのポイント.png": "./picture/idem_ts_study_023_key_points_here.png",
    "./picture/idem_ts_study_023_発展①fastcheckプロパティベーステストで_変な入力_を自動生成.png": "./picture/idem_ts_study_023_advanced1_fastcheck_property_based_testing_auto_generate_weird_inputs.png",
    "./picture/idem_ts_study_023_1_テスト観点を増やす.png": "./picture/idem_ts_study_023_1_increase_test_perspectives.png",
}

files = [
    'docs/picture/image_generation_plan.md',
    'docs/idem_ts_study_017.md',
    'docs/idem_ts_study_018.md',
    'docs/idem_ts_study_019.md',
    'docs/idem_ts_study_020.md',
    'docs/idem_ts_study_021.md',
    'docs/idem_ts_study_022.md',
    'docs/idem_ts_study_023.md'
]

for file_path in files:
    if not os.path.exists(file_path):
        print(f"Skipping {file_path} (not found)")
        continue
    
    print(f"Processing {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old, new in rename_map.items():
            if old in content:
                content = content.replace(old, new)
                print(f"  Replaced: {old} -> {new}")
            
            # Special case: The files in `docs/` might point to `picture/` so the path prefix matches the map directly.
            # But `docs/picture/image_generation_plan.md` might also have `./picture/` prefix if user put it there?
            # Or it might be just filename without `./picture/`. 
            # In image_generation_plan.md, the lines might look like `![...](idem_ts_study_...png)` or `![...](./picture/...)`
            # The rename_map keys have `./picture/` prefix.
            # I should ALSO check for the version WITHOUT `./picture/` prefix just in case, but map to the new filename without prefix.
            
            old_base = os.path.basename(old)
            new_base = os.path.basename(new)
            
            if old_base in content and old not in content: # Avoid double replace if `old` is `foo` and we have `./picture/foo`
                 # Only replace if it matches exactly the basename, e.g. in `image_generation_plan.md` which is IN `docs/picture/` so it might reference files directly?
                 # Actually, `image_generation_plan.md` in `docs/picture` likely references headers or plans, maybe not actual image links?
                 # If it lists filenames as text, they might be just basenames.
                 content = content.replace(old_base, new_base)
                 print(f"  Replaced basename: {old_base} -> {new_base}")

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {file_path}")
        else:
            print(f"No changes in {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
