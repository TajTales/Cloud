export type VocabularyEntry = {
  word: string;
  kana: string;
  romaji: string;
  partOfSpeech: string;
  meaning: string;
  usage: string;
  example: string;
  exampleTranslation: string;
  lemma?: string;
  lemmaReading?: string;
  lemmaMeaning?: string;
};

// Curated entries for the two existing demo transcript lines, not automatic OCR analysis.
export const transcriptVocabulary: VocabularyEntry[] = [
  { word: "すみません", kana: "すみません", romaji: "sumimasen", partOfSpeech: "Cách nói lịch sự", meaning: "Xin lỗi; làm phiền một chút.", usage: "Dùng để xin lỗi hoặc mở đầu khi muốn hỏi, nhờ ai đó. Trong câu này, người nói muốn hỏi đường.", example: "すみません、駅はどこですか。", exampleTranslation: "Xin lỗi, nhà ga ở đâu ạ?" },
  { word: "この", kana: "この", romaji: "kono", partOfSpeech: "Từ chỉ định", meaning: "Này; cái này (đứng trước danh từ).", usage: "Đi cùng danh từ: この + danh từ. この近く nghĩa là gần đây, gần chỗ này.", example: "この本はおもしろいです。", exampleTranslation: "Cuốn sách này thú vị." },
  { word: "近く", kana: "ちかく", romaji: "chikaku", partOfSpeech: "Danh từ / trạng từ", meaning: "Gần; khu vực lân cận.", usage: "Trong この近くに, chỉ một địa điểm gần chỗ người nói. Dạng tính từ liên quan là 近い (ちかい).", example: "駅の近くに住んでいます。", exampleTranslation: "Tôi sống gần nhà ga." },
  { word: "に", kana: "に", romaji: "ni", partOfSpeech: "Trợ từ", meaning: "Ở; tại (trong ngữ cảnh này).", usage: "Đánh dấu nơi một vật hoặc người tồn tại khi đi với ある / いる. 近くにあります = có ở gần đây.", example: "机の上に本があります。", exampleTranslation: "Có một cuốn sách trên bàn." },
  { word: "おすすめ", kana: "おすすめ", romaji: "osusume", partOfSpeech: "Danh từ", meaning: "Sự giới thiệu; điều được đề xuất.", usage: "おすすめの + danh từ: một thứ được giới thiệu, đáng thử. Trong câu này là quán cà phê mà người nghe muốn giới thiệu.", example: "おすすめの料理は何ですか。", exampleTranslation: "Bạn có món ăn nào muốn giới thiệu không?" },
  { word: "の", kana: "の", romaji: "no", partOfSpeech: "Trợ từ", meaning: "Nối danh từ; bổ nghĩa cho danh từ phía sau.", usage: "Trong おすすめのカフェ, nối おすすめ với カフェ, nghĩa là quán cà phê được đề xuất.", example: "これは私の本です。", exampleTranslation: "Đây là sách của tôi." },
  { word: "カフェ", kana: "カフェ", romaji: "kafe", partOfSpeech: "Danh từ", meaning: "Quán cà phê.", usage: "Từ mượn được viết bằng katakana. Thường dùng cho quán cà phê theo phong cách hiện đại.", example: "カフェで勉強します。", exampleTranslation: "Tôi học ở quán cà phê." },
  { word: "は", kana: "わ", romaji: "wa", partOfSpeech: "Trợ từ chủ đề", meaning: "Nêu chủ đề đang được nói tới.", usage: "Khi là trợ từ, は được đọc là wa. Trong câu này, người nói đưa quán cà phê vào làm chủ đề để hỏi.", example: "私は学生です。", exampleTranslation: "Tôi là sinh viên." },
  { word: "あります", kana: "あります", romaji: "arimasu", partOfSpeech: "Động từ · thể lịch sự", meaning: "Có; tồn tại (đồ vật hoặc địa điểm).", lemma: "ある", lemmaReading: "ある", usage: "Dạng lịch sự của ある. 喫茶店があります = có một quán cà phê. Khi nói về người hoặc động vật, thường dùng います.", example: "公園に池があります。", exampleTranslation: "Có một cái ao trong công viên." },
  { word: "か", kana: "か", romaji: "ka", partOfSpeech: "Trợ từ nghi vấn", meaning: "Đánh dấu câu hỏi.", usage: "Đặt cuối câu, thường sau thể lịch sự. ありますか nghĩa là có ... không?", example: "日本語がわかりますか。", exampleTranslation: "Bạn có hiểu tiếng Nhật không?" },
  { word: "はい", kana: "はい", romaji: "hai", partOfSpeech: "Thán từ / lời đáp", meaning: "Vâng; có.", usage: "Lời đáp lịch sự để xác nhận hoặc cho biết mình đang lắng nghe. Nghĩa cụ thể phụ thuộc câu hỏi trước đó.", example: "はい、わかりました。", exampleTranslation: "Vâng, tôi hiểu rồi." },
  { word: "角", kana: "かど", romaji: "kado", partOfSpeech: "Danh từ", meaning: "Góc; góc đường.", usage: "Trong 角を曲がる, 角 đọc là かど (kado), chỉ góc đường để rẽ.", example: "次の角を右に曲がってください。", exampleTranslation: "Hãy rẽ phải ở góc đường tiếp theo." },
  { word: "を", kana: "お", romaji: "o", partOfSpeech: "Trợ từ", meaning: "Đánh dấu đối tượng hoặc nơi đi qua.", usage: "を được đọc là o. Trong 角を曲がる, chỉ vị trí mà người đi thực hiện động tác rẽ.", example: "橋を渡ります。", exampleTranslation: "Tôi đi qua cầu." },
  { word: "曲がった", kana: "まがった", romaji: "magatta", partOfSpeech: "Động từ · thể た", meaning: "Đã rẽ; đã quẹo.", lemma: "曲がる", lemmaReading: "まがる", lemmaMeaning: "Rẽ; quẹo.", usage: "Thể た của động từ nhóm 1 曲がる. Trong 曲がったところ, bổ nghĩa cho ところ: chỗ vừa rẽ qua.", example: "角を曲がったところに店があります。", exampleTranslation: "Có một cửa hàng ở chỗ vừa rẽ qua góc đường." },
  { word: "ところ", kana: "ところ", romaji: "tokoro", partOfSpeech: "Danh từ", meaning: "Chỗ; nơi; địa điểm.", usage: "Trong câu này, chỉ địa điểm sau khi rẽ. Thường được viết bằng hiragana; cũng có dạng chữ Hán 所.", example: "ここは静かなところです。", exampleTranslation: "Đây là một nơi yên tĩnh." },
  { word: "静かな", kana: "しずかな", romaji: "shizuka na", partOfSpeech: "Tính từ な", meaning: "Yên tĩnh; êm ả.", lemma: "静か", lemmaReading: "しずか", usage: "静か thêm な khi đứng trước danh từ: 静かな喫茶店 = một quán cà phê yên tĩnh. Khi lưu, dùng dạng gốc 静か.", example: "静かな部屋で本を読みます。", exampleTranslation: "Tôi đọc sách trong căn phòng yên tĩnh." },
  { word: "喫茶店", kana: "きっさてん", romaji: "kissaten", partOfSpeech: "Danh từ", meaning: "Quán cà phê; quán giải khát.", usage: "きっさてん có âm ngắt nhỏ っ, đọc giữ phụ âm s một nhịp. Thường gợi quán cà phê kiểu truyền thống.", example: "喫茶店でコーヒーを飲みます。", exampleTranslation: "Tôi uống cà phê ở quán." },
  { word: "が", kana: "が", romaji: "ga", partOfSpeech: "Trợ từ chủ ngữ", meaning: "Đánh dấu chủ ngữ của câu.", usage: "Trong 喫茶店があります, が đánh dấu sự vật tồn tại: có một quán cà phê.", example: "庭に花があります。", exampleTranslation: "Có hoa trong vườn." },
];

export type TranscriptToken = { text: string; entry?: VocabularyEntry };

export function tokenizeTranscript(text: string, romaji = false): TranscriptToken[] {
  const entries = [...transcriptVocabulary].sort((a, b) => (romaji ? b.romaji.length - a.romaji.length : b.word.length - a.word.length));
  const tokens: TranscriptToken[] = [];
  let plain = "";
  for (let index = 0; index < text.length;) {
    const entry = entries.find(item => {
      const term = romaji ? item.romaji : item.word;
      if (text.slice(index, index + term.length).toLowerCase() !== term.toLowerCase()) return false;
      return !romaji || (!/[a-z]/i.test(text[index - 1] || "") && !/[a-z]/i.test(text[index + term.length] || ""));
    });
    if (!entry) { plain += text[index++]; continue; }
    if (plain) { tokens.push({ text: plain }); plain = ""; }
    const length = romaji ? entry.romaji.length : entry.word.length;
    tokens.push({ text: text.slice(index, index + length), entry });
    index += length;
  }
  if (plain) tokens.push({ text: plain });
  return tokens;
}
