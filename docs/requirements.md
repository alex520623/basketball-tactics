# 需求與簡報比較

## 來源與優先順序

檢閱日期：2026-11-12。兩份簡報均已透過 Google Drive 讀取原生文字、講者備註及渲染頁面。
規格衝突時，以 Proposal v6 為準；文中另外提出的驗收細節屬工程建議。

| 代號 | 來源 | 頁數 | Drive 修改日期（UTC） | 讀取 revision |
| --- | --- | --- | --- | --- |
| H | [HW1_MM](https://docs.google.com/presentation/d/12cZ5et1jqkYHCjjmQn6CA1QOufa8s1Z1ouo9Fy2fTT8/edit) | 19 | 2026-10-19 | `qUV7kkv2M-AXWA` |
| P | [Basketball_Tactical_Analysis_Video_Proposal_v6](https://docs.google.com/presentation/d/1LyysX5R2Rx2TAFa60LjtwqHenY_ZosrGIBHIkpO26rw/edit) | 6 | 2026-10-31 | `QPrZ3Doagzf8aw` |

以下摘要反映簡報內容。文獻的書目、引用次數與研究結果未在此次工作中另外查核，不應將
簡報中的比較圖視為實測排名，也不應把文獻能力直接當成本專案已具備的功能。

## HW1：研究與完整系統構想

H 第 1 頁為課程與組別。第 2–13 頁整理 12 篇研究，主要關注軌跡、場上空間關係、
戰術辨識及可解釋的決策分析：

| 頁碼 | 簡報所列研究 | 對本專案的啟發 |
| --- | --- | --- |
| H2 | Cervone et al. (2016), A Multiresolution Stochastic Process Model for Predicting Basketball Possession Outcomes | 由追蹤狀態估計 EPV，連接時空資料與決策價值 |
| H3 | Chen et al. (2012), Recognizing tactic patterns in broadcast basketball video using player trajectory | 影片、座標轉換與軌跡可作為戰術辨識流程 |
| H4 | Franks et al. (2015), Characterizing the spatial structure of defensive skill in professional basketball | 防守影響需要考慮空間位置與壓力 |
| H5 | Diao, GameSense（簡報列 2025） | 階層式時空模型描述短期動作與較長期配合 |
| H6 | Pointwise (2014) | 以追蹤資訊比較傳球、運球與出手選擇的價值 |
| H7 | Stephanos et al. (2021), Machine learning predictive analytics for player movement prediction in NBA | 由過往軌跡預測移動的可能性與限制 |
| H8 | Bao（簡報列 2026）, Analysis of decision support system of basketball sports competition based on machine learning and IoT | 整合特徵與時空資訊支援戰術評估 |
| H9 | Pan et al. (2023), Offensive Tactics Recognition in Broadcast Basketball Videos Based on 2D Camera View Player Heatmaps | 可透過熱力圖表示移動，不必每次重建精確俯視場地 |
| H10 | Xu et al.（簡報列 2023）, Recognition of basketball tactics based on vision transformer and track filter | 軌跡與視覺時空模型可用於分類 |
| H11 | Chang（簡報列 2026）, Construction of tactical decision knowledge graph and explainable reasoning for dynamic basketball offense and defense | 知識與關係表示支持有依據的解釋 |
| H12 | Perše et al. (2009), A trajectory-based analysis of coordinated team activity in a basketball game | 團隊活動需要分析跨球員、跨時間的協作 |
| H13 | Skinner and Guy (2015), A method for using player tracking data in basketball to learn player skills and predict team performance | 球員互動與個別能力會影響團隊表現 |

H 第 14–17 頁為心智圖、function-and-form、form 樹狀整理與優缺點的工作坊照片，呈現
以影片、軌跡、追蹤及多來源資訊整理研究的過程。部分手寫便條在照片中無法可靠辨讀，
不將未辨識的文字轉成需求。第 18 頁以「資料需求與部署成本」和「分析深度與決策支援程度」
比較研究方向，供選擇實作取捨。

H 第 19 頁的架構為：

1. 輸入一段籃球比賽影片，經影格切割、影像擷取與畫面校正。
2. 球場校正與 Homography 轉為 2D 俯視；另由球員／球偵測與多目標追蹤取得位置。
3. 建立 2D 場地座標、球員與球資訊及關係圖，再分析移動、站位與傳導等關係。
4. 知識庫與評估規則提供定義、專家規則與歷史案例，支援 ChatGPT 模組的戰術辨識、
   評估與建議生成；圖中舉 Pick-and-Roll、Off-ball Screen、Horns、Isolation 為辨識例子。
5. 中間結果包含 2D 俯視、球員編號與軌跡，以及戰術分析結果；最後輸出戰術文字與修正建議。

上述戰術名稱是早期構想的例子，不代表目前資料集已有這些標籤，也不是 S1 分類清單。

## Proposal v6：需求與分階段交付

| 頁碼 | 內容 | 對開發的約束 |
| --- | --- | --- |
| P1 | 既有資料集＋時空表示＋LLM 解釋 | 以既有球員追蹤資訊起步 |
| P2 | N1 影片分析耗時、N2 多人配合難理解、N3 數據難轉成說明 | 目標為教練、球員與學習者；需求仍是設計假設，尚非已驗證結論 |
| P3 | D1 既有資料、D2 球場座標、D3 時空資訊、D4 軌跡／戰術分析、D5 知識與規則、D6 LLM 解釋 | 先整理可用資料與判讀依據；有標註才嘗試少數戰術分類 |
| P4 | 設計空間比較影片／熱力圖、追蹤＋EPV、知識圖譜 | 提案位置是待驗證的概念，不宣稱跨論文效能優勢 |
| P5 | System Framework、S1／S2／S3 與 Ultimate Goal | 每階段可展示，至少交付 S1；影片處理保留為後續擴充 |
| P6 | 選片段、看空間／軌跡、理解說明、後續追問；標籤或人工評估 | 依階段提供介面，記錄誤判及解釋是否符合實際軌跡 |

最新資料流程為「既有籃球追蹤資料 → 資料整理與座標標準化 → 時空表示與軌跡資訊」，
再逐步交付：

- **S1**：2D 球場、球員位置、移動軌跡與時間變化，是最低完成目標。
- **S2**：分析球員相對位置與跑位模式；標註適當時才嘗試少數戰術辨識，可不依賴 LLM 展示。
- **S3**：將分析證據與戰術知識／規則交給 LLM，先生成有依據的解釋。
- **最終目標**：完整自動戰術辨識、空間與跑位評估、解釋與改善建議。互動追問屬後續規劃。

球位置是「可用時包含」，不是無條件的 S1 前置需求。兩份簡報均未提供已選資料集的
明確名稱、下載來源、欄位格式或授權；本規劃保留該資料集，等待確認。

使用者後續指定 SportVU 公開 repository 作為調查候選，單場格式與適用性已整理在
[資料評估](sportvu-assessment.md)。此補充不代表簡報原先已列出該來源，也不代表已正式採用。

## 兩版差異與採用範圍

| 面向 | HW1 | Proposal v6 | 實作規劃 |
| --- | --- | --- | --- |
| 主要輸入 | 影片片段 | 既有追蹤資料，球位置可選 | 先做選定資料集的 importer |
| 視覺前處理 | 校正、Homography、偵測與追蹤在主流程 | 影片輸入時才需要 | 移出 S1 必做清單 |
| 中間表示 | 2D 座標、軌跡、關係圖 | 保留並強調資料／時間標準化 | 先建立可驗證的共同資料規格 |
| 戰術辨識 | 完整模組構想，含多種戰術例子 | 有適合標註才嘗試少數類別 | 無標註時先做描述性分析 |
| LLM 角色 | 圖中涵蓋辨識、評估與建議 | S3 著重解釋判斷依據 | 分析證據由 Backend 產生，LLM 負責文字化解釋 |
| 建議與追問 | 修正建議為完整輸出構想 | 改善建議為最終目標，追問後續規劃 | 不列入 S1 驗收 |
| 最低交付 | 展示完整流程構想 | 明確至少交付 S1 | 先讓真實片段可載入、播放與顯示軌跡 |
| 評估 | 文獻與設計取捨 | 標籤／人工判讀、軌跡一致性、誤判案例 | 將驗收分成資料、畫面與分析證據 |

EPV、深度模型、完整知識圖譜、影片上傳處理與即時辨識均非最新提案的最低要求；
是否加入，應在 S1 完成後依資料與課程時間另行決定。

## 需求對照

| ID | 需求 | 階段 | 來源 | 可檢查的結果 |
| --- | --- | --- | --- | --- |
| R1 | 使用原先選定的既有追蹤資料 | S1 | P3 D1、P5 INPUT；使用者限制 | 資料來源、版本、授權與 sample 已記錄 |
| R2 | 統一時間、球場座標與缺漏處理 | S1 | P3 D2、P5 PREP | 有來源到標準欄位的對照與轉換驗證 |
| R3 | 呈現 2D 球場、球員位置與軌跡的時間變化 | S1 最低交付 | P5 S1、P6 | 至少一段真實資料可獨立展示 |
| R4 | 選擇片段、檢視時間變化 | S1 互動 | P6 預計流程 | 播放／暫停、時間拖曳與片段選擇；控制細節為工程建議 |
| R5 | 描述球員時空關係與跑位模式 | S2 | P3 D3／D4、P5 S2 | 可追溯至球員、時間範圍與量測值 |
| R6 | 視標註嘗試少數戰術辨識 | S2 條件式 | P3 D4、P5 S2 | 確認標籤與評估方式後才設定分類目標 |
| R7 | 知識規則與分析證據約束 LLM 解釋 | S3 | P3 D5／D6、P5 S3 | 說明引用實際證據，資料不足時明示限制 |
| R8 | 與標籤／人工判讀比較並記錄錯誤 | S2／S3 | P6 評估 | 保存案例、判讀依據、誤判與不一致說明 |
| R9 | 進階階段無法完成時保留 S1 展示 | 全階段 | P5 備援、P6 最低目標 | S1 不需要模型、標籤或 LLM API 才能運作 |

工程上的具體驗收項目見 [S1 計畫](s1-plan.md)。那些門檻是為落實以上需求而提出，
不是簡報中已經承諾或驗證的效能數字。
