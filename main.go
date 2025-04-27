package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"golang.org/x/time/rate"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

var (
	GlobalCache *Cache
	once        sync.Once
	BasePath, _ = os.Getwd()
	// 初始化 rate.Limiter：5 QPS，最大突发 15
	limiter           = rate.NewLimiter(rate.Every(300*time.Millisecond), 300)
	DeepseekApiKey    = "sk-7ad5506da36d4dd5b88d7c3d2ea010ca"
	promptForClassify = `请严格按以下规则处理德语文本：
1. 提取所有名词，动词，形容词副词，专有名词，并还原为原型（动词不定式/名词单数主格/形容词原级）
2. 名词保持首字母大写，复合词不拆解（如"Schulbuch"不拆）
3. 去除重复项，返回唯一词列表
4. 仅输出字符串结果，单词间用换行符隔开，格式示例：
"Wort1
Wort2
Wort3
……"

输入文本：
`
	promptForNotizen = `请按照以下规则处理德语文本：
1. **结构要求**
- 按此顺序呈现：
[德语原文] → [中文翻译] → [固定搭配和习惯用语标注]
2. **标注规范**
- 固定搭配和习惯用语用**加粗**标出，格式：**原词**（中文解释）
- 专业术语附加括号注原文，例：镜像神经元（Spiegelneuronen）
- 尽可能多的找出固定搭配和习惯用语
3. **扩展逻辑**
- 若句子含多个搭配，分行列举
- 文化特定表达需说明背景，例："Murmelgruppe"需注"源自德国教学法"
4. **风格控制**
- 中文翻译采用学术口语混合风格
- 避免直译，优先传达功能意图
5. **格式要求**
- 仅返回处理结果，不要添加任何额外的文字或解释，不要包括任何格式文本框
    - 返回的大致格式就是
    "[德语原文]
    xxxxxxxx
    [中文翻译] 
    xxxxxxxx
    [固定搭配标注]
    xxxxxxxx  "

**执行优先级**：保留原文完整性 > 搭配标注准确性 > 翻译可读性
以下是需要处理的文本：
`
	promptForOrganize = `请严格按以下规则处理德语文本,：
1. 将输入的文本排版为自然段落 （也就是说你要处理换行，表格之类的，导致文本中断的情况）
2. 仅输出结果，一个str值

以下输入文本：
`
	promptForFormat = `请将以下提供的德语单词区分出动词、名词、形容词副词，专有名词，分析并填入下列模版，以Markdown格式返回。要求：  
1. 名词需标注词性（der/die/das）  
2. 所有单词提供中文翻译  
3. 仅返回结果，不要添加任何额外的文字或解释，也不要添加任何形式的文本格式框。
4. 每一行是一个单词按以下格式返回：
- (Verben)/(Nomen)/(Adjektive)/(Adverbien)/(Eigennamen) der/die/das(如果是名词的话) 单词 - 翻译
- …………
- …………

以下是待处理单词：
`
)

func GetFormattedTimestamp() string {
	now := time.Now()
	return fmt.Sprintf("%04d:%02d:%02d:%02d:%02d:%02d:%09d",
		now.Year(),
		now.Month(),
		now.Day(),
		now.Hour(),
		now.Minute(),
		now.Second(),
		now.Nanosecond()) // 直接使用纳秒
}

func GetRequestType(prompt string) string {
	switch prompt {
	case promptForClassify:
		return "classify"
	case promptForNotizen:
		return "notizen"
	case promptForOrganize:
		return "organize"
	case promptForFormat:
		return "format"
	default:
		return "unknown"
	}
}

type Cache struct {
	sync.RWMutex
	data  map[string]string
	path  string
	count int
}

// 初始化全局缓存单例
func initCache() {
	once.Do(func() {
		cachePath := filepath.Join(BasePath, "Cache", "requests_cache.json")
		GlobalCache = &Cache{
			data:  make(map[string]string),
			path:  cachePath,
			count: 0,
		}
		GlobalCache.Load()
	})
}

// Get 读取缓存值
func (c *Cache) Get(key string) (string, bool) {
	c.RLock()
	defer c.RUnlock()
	val, exists := c.data[key]
	return val, exists
}

// Set 写入缓存值
func (c *Cache) Set(key, value string) {
	c.Lock()
	defer c.Unlock()
	c.data[key] = value
}

// Save 保存缓存到文件
func (c *Cache) Save() error {
	c.RLock()
	defer c.RUnlock()

	// 确保目录存在
	dir := filepath.Dir(c.path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("创建缓存目录失败: %v", err)
	}

	// 将数据编码为JSON
	data, err := json.Marshal(c.data)
	if err != nil {
		return fmt.Errorf("序列化缓存数据失败: %v", err)
	}

	// 写入文件
	if err := os.WriteFile(c.path, data, 0644); err != nil {
		return fmt.Errorf("写入缓存文件失败: %v", err)
	}

	return nil
}
func (c *Cache) SavePer() error {
	c.RLock()
	defer c.RUnlock()
	if c.count >= 15 {
		c.count = 0
		dir := filepath.Dir(c.path)
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("创建缓存目录失败: %v", err)
		}

		// 将数据编码为JSON
		data, err := json.Marshal(c.data)
		if err != nil {
			return fmt.Errorf("序列化缓存数据失败: %v", err)
		}

		// 写入文件
		if err := os.WriteFile(c.path, data, 0644); err != nil {
			return fmt.Errorf("写入缓存文件失败: %v", err)
		}
	} else {
		c.count++
	}
	return nil
}

// Load 从文件加载缓存
func (c *Cache) Load() {
	c.Lock()
	defer c.Unlock()

	// 读取文件
	data, err := os.ReadFile(c.path)
	if err != nil {
		if !os.IsNotExist(err) {
			log.Printf("读取缓存文件失败: %v", err)
		}
		c.data = make(map[string]string)
		return
	}

	// 解析JSON
	if err := json.Unmarshal(data, &c.data); err != nil {
		log.Printf("解析缓存文件失败: %v", err)
		c.data = make(map[string]string)
		return
	}
}

type Project struct {
	projectName string
	targetDir   string
}

// NewProject 初始化时接收一个字符串变量并设置属性，同时结合全局变量 BasePath
func NewProject(name string) *Project {
	fmt.Printf("<UNK> %s <UNK>...\n", name)
	initCache()
	return &Project{
		targetDir: filepath.Join(BasePath, name),
	}
}

// NewProjectWithPath 通过绝对路径初始化 Project
func NewProjectWithPath(absolutePath string) *Project {
	fmt.Printf("<UNK> %s <UNK>...\n", absolutePath)
	initCache()
	return &Project{
		projectName: filepath.Base(absolutePath),
		targetDir:   absolutePath,
	}
}

// Run 遍历 BasePath 目录下 name 文件夹浅层目录下的所有文件夹，并打印绝对目录
func (p *Project) Run() {

	dirPath := p.targetDir

	// 检查目标目录是否存在
	if _, err := os.Stat(dirPath); os.IsNotExist(err) {
		fmt.Printf("目录 %s 不存在，正在创建...\n", dirPath)
		if err := os.MkdirAll(dirPath, os.ModePerm); err != nil {
			log.Fatalf("创建目录失败: %v", err)
			return
		}
	}

	// 读取目标目录的内容
	entries, err := os.ReadDir(dirPath)
	if err != nil {
		log.Fatalf("读取目录失败: %v", err)
	}
	folderList := make([]string, 0)
	// 遍历并打印所有子文件夹的绝对路径
	for _, entry := range entries {
		if entry.IsDir() {
			absPath, err := filepath.Abs(filepath.Join(dirPath, entry.Name()))
			if err != nil {
				log.Printf("获取绝对路径失败: %v", err)
				continue
			}
			folderList = append(folderList, absPath)
		}
	}
	ProcessArray(folderList, func(path string) bool {
		NewFolder(path).Run()
		return true
	})
	// 保存缓存到文件
	_ = GlobalCache.Save()
}

type Folder struct {
	absolutePath string
}

// NewFolder 初始化时接收一个绝对地址并设置属性
func NewFolder(path string) *Folder {
	fmt.Printf("<UNK> %s <UNK>...\n", path)
	initCache()
	return &Folder{
		absolutePath: path,
	}
}

// Run 按文件名顺序遍历前目录下的所有文件夹的绝对地址
func (f *Folder) Run() {
	entries, err := os.ReadDir(f.absolutePath)
	if err != nil {
		log.Fatalf("读取目录失败: %v", err)
	}

	// 按文件名排序
	sort.Slice(entries, func(i, j int) bool {
		return entries[i].Name() < entries[j].Name()
	})

	// 遍历并打印所有子文件夹的绝对路径
	partList := make([]string, 0)
	for _, entry := range entries {
		if entry.IsDir() {
			absPath, err := filepath.Abs(filepath.Join(f.absolutePath, entry.Name()))
			if err != nil {
				log.Printf("获取绝对路径失败: %v", err)
				continue
			}
			partList = append(partList, absPath)
		}
	}
	setFromPart := ProcessArray(partList, func(path string) map[string]bool {
		return NewPart(path).Run()
	})
	existedSet := make(map[string]bool)
	diffNewSetList := make([]map[string]bool, 0)
	diffOldSetList := make([]map[string]bool, 0)
	for _, currentSet := range setFromPart {
		diffNewSetList = append(diffNewSetList, difference(currentSet, existedSet))
		diffOldSetList = append(diffOldSetList, intersection(currentSet, existedSet))
		existedSet = union(existedSet, currentSet)
	}
	var wg sync.WaitGroup
	var NewMdTextList, OldMdTextList []string

	wg.Add(2)
	go func() {
		defer wg.Done()
		NewMdTextList = ProcessArray(diffNewSetList, askDeepSeekFormat)
	}()
	go func() {
		defer wg.Done()
		OldMdTextList = ProcessArray(diffOldSetList, askDeepSeekFormat)
	}()
	wg.Wait()
	for i := 0; i < len(partList); i++ {
		err := NewPart(partList[i]).saveResultToFile(NewMdTextList[i], "new")
		if err != nil {
			log.Fatalf("<UNK>: %v", err)
		}
		err = NewPart(partList[i]).saveResultToFile(OldMdTextList[i], "old")
		if err != nil {
			log.Fatalf("<UNK>: %v", err)
		}

	}
	_ = GlobalCache.Save()
}

type Part struct {
	absolutePath string
}

// NewPart 初始化时接收一个绝对地址并设置属性
func NewPart(path string) *Part {
	fmt.Printf("<UNK> %s <UNK>...\n", path)
	return &Part{
		absolutePath: path,
	}
}

// Run 遍历打印浅目录下所有的文件绝对地址（不包括文件夹）
func (p *Part) Run() map[string]bool {
	// 读取目录内容
	entries, err := os.ReadDir(p.absolutePath)
	if err != nil {
		log.Fatalf("读取目录失败: %v", err)
	}

	// 遍历并打印所有文件的绝对路径（排除文件夹）
	fileList := make([]string, 0)
	for _, entry := range entries {
		if !entry.IsDir() {
			absPath, err := filepath.Abs(filepath.Join(p.absolutePath, entry.Name()))
			if err != nil {
				log.Printf("获取绝对路径失败: %v", err)
				continue
			}
			fileList = append(fileList, absPath)
		}

	}
	wordSetList := ProcessArray(fileList, func(path string) map[string]bool {
		return NewFile(path).Run()
	})
	// 合并所有的 map[string]bool
	mergedSet := make(map[string]bool)
	for _, set := range wordSetList {
		mergedSet = union(mergedSet, set)
	}
	return mergedSet

}

func (p *Part) saveResultToFile(resultString string, name string) error {
	// 创建 result 文件夹路径
	resultDir := filepath.Join(p.absolutePath, "result")

	// 检查 result 文件夹是否存在，不存在则创建
	if _, err := os.Stat(resultDir); os.IsNotExist(err) {
		if err := os.MkdirAll(resultDir, os.ModePerm); err != nil {
			return fmt.Errorf("创建 result 文件夹失败: %v", err)
		}
	}

	// 构造目标文件路径
	filePath := filepath.Join(resultDir, name+".md")

	// 将内容写入文件
	if err := os.WriteFile(filePath, []byte(resultString), 0644); err != nil {
		return fmt.Errorf("写入文件失败: %v", err)
	}

	return nil
}

type File struct {
	absolutePath string
}

// NewFile 初始化时接收一个文件的绝对地址并设置属性
func NewFile(path string) *File {
	return &File{
		absolutePath: path,
	}
}

// Run 打印文件的绝对地址和文件大小
func (f *File) Run() map[string]bool {
	// 读取文件内容为字符串数组
	lines, err := f.readFileToLines()
	if err != nil {
		log.Fatalf("读取文件失败: %v", err)
	}
	lines = f.processLinesOrganize(lines)

	var wg sync.WaitGroup
	var resultString string
	var hashTable map[string]bool

	wg.Add(2)
	go func() {
		defer wg.Done()
		resultString = f.processLinesToNotizen(lines)
	}()
	go func() {
		defer wg.Done()
		hashTable = f.processLinesToClassifyHash(lines)
	}()
	wg.Wait()

	// 提取当前文件名（不含扩展名）
	fileName := strings.TrimSuffix(filepath.Base(f.absolutePath), filepath.Ext(f.absolutePath))

	// 将第一个函数返回的字符串保存到 result 文件夹中
	err = f.saveResultToFile(resultString, fileName)
	if err != nil {
		log.Fatalf("保存结果失败: %v", err)
	}

	return hashTable
}

func (f *File) processLinesOrganize(lines []string) []string {
	return ProcessArray(lines, func(text string) string {
		return askDeepSeek(promptForOrganize, text)
	})
}

func (f *File) processLinesToNotizen(lines []string) string {
	lst := ProcessArray(lines, func(text string) string {
		return askDeepSeek(promptForNotizen, text)
	})
	return strings.Join(lst, "\n************************\n")
}

func (f *File) processLinesToClassifyHash(lines []string) map[string]bool {
	stringList := ProcessArray(lines, func(text string) string {
		return askDeepSeek(promptForClassify, text)
	})
	sets := make([]map[string]bool, 0)
	for _, str := range stringList {
		set := make(map[string]bool, 0)
		for _, word := range strings.Split(str, "\n") {
			if word != "" {
				set[word] = true
			}
		}
		sets = append(sets, set)
	}
	ans := make(map[string]bool)
	for _, set := range sets {
		for key, _ := range set {
			ans[key] = true
		}
	}
	return ans
}

// readFileToLines 根据文件类型提取文本
func (f *File) readFileToLines() ([]string, error) {
	var lines []string

	// 判断文件类型
	ext := filepath.Ext(f.absolutePath)
	if ext == ".pdf" {
		// 使用 pdfcpu 提取 PDF 文本
		text, err := extractTextFromPDF(f.absolutePath)
		if err != nil {
			return nil, fmt.Errorf("提取 PDF 文本失败: %v", err)
		}

		// 按页分割并添加到 lines
		lines = append(lines, text...)
	} else {
		// 处理其他文件类型
		file, err := os.Open(f.absolutePath)
		if err != nil {
			return nil, fmt.Errorf("无法打开文件: %v", err)
		}
		defer file.Close()

		scanner := bufio.NewScanner(file)
		var group []string
		for scanner.Scan() {
			group = append(group, scanner.Text())
			if len(group) == 10 {
				lines = append(lines, strings.Join(group, "\n"))
				group = nil
			}
		}
		// 添加剩余的行
		if len(group) > 0 {
			lines = append(lines, strings.Join(group, "\n"))
		}

		if err := scanner.Err(); err != nil {
			return nil, fmt.Errorf("读取文件失败: %v", err)
		}
	}

	return lines, nil
}

func (f *File) saveResultToFile(resultString string, name string) error {
	// 创建 result 文件夹路径
	resultDir := filepath.Join(filepath.Dir(f.absolutePath), "result")

	// 检查 result 文件夹是否存在，不存在则创建
	if _, err := os.Stat(resultDir); os.IsNotExist(err) {
		if err := os.MkdirAll(resultDir, os.ModePerm); err != nil {
			return fmt.Errorf("创建 result 文件夹失败: %v", err)
		}
	}

	// 构造目标文件路径
	filePath := filepath.Join(resultDir, name+".md")

	// 将内容写入文件
	if err := os.WriteFile(filePath, []byte(resultString), 0644); err != nil {
		return fmt.Errorf("写入文件失败: %v", err)
	}

	return nil
}

func extractTextFromPDF(pdfPath string) ([]string, error) {
	// 调用 Python 脚本并传入 PDF 文件路径作为参数
	cmd := exec.Command("python3", "extract_words_from_pdf.py", pdfPath)
	// 获取输出
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Println("出错了:", err)
		fmt.Println("Python脚本输出:", string(output)) // 打印出 Python 报错信息
		return nil, err
	}
	// 解析 Python 返回的 JSON 数据
	var result []string
	err = json.Unmarshal(output, &result)
	if err != nil {
		return nil, fmt.Errorf("无法解析 JSON 数据: %v", err)
	}

	return result, nil
}

type ResponseData struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}

func askDeepSeekFormat(set map[string]bool) string {
	texts := make([]string, 0)
	for text, _ := range set {
		texts = append(texts, text)
	}
	sort.Strings(texts)
	ans := make([]string, 0)
	for len(texts) > 250 {
		text := texts[:250]
		ans = append(ans, strings.Join(text, "\n"))
		texts = texts[250:]
	}
	ans = append(ans, strings.Join(texts, "\n"))
	mdPiece := ProcessArray(ans, func(text string) string {
		return askDeepSeek(promptForFormat, text)
	})
	finalTexts := make([]string, 0)
	for _, text := range mdPiece {
		finalTexts = append(finalTexts, strings.Split(text, "\n")...)
	}
	sort.Strings(finalTexts)
	return strings.Join(finalTexts, "\n")
}

type RequestData struct {
	Model    string `json:"model"`
	Messages []struct {
		Role    string `json:"role"`
		Content string `json:"content"`
	} `json:"messages"`
}

func askDeepSeek(prompt string, text string) string {
	// 替换成你的实际 API 密钥
	content := prompt + text
	value, exists := GlobalCache.Get(content)
	if exists {
		fmt.Println(GetFormattedTimestamp(), "命中缓存: ", GetRequestType(prompt), " ", strings.Replace(text, "\n", " ", -1))
		return value
	} // 等待令牌
	if err := limiter.Wait(context.Background()); err != nil {
		log.Printf("限流等待失败: %v", err)
	}
	apiKey := DeepseekApiKey
	fmt.Println(GetFormattedTimestamp(), "新网络请求: ", GetRequestType(prompt), " ", strings.Replace(text, "\n", " ", -1))
	// API 端点
	url := "https://api.deepseek.com/v1/chat/completions"

	// 构造请求体
	requestData := RequestData{
		Model: "deepseek-chat",
		Messages: []struct {
			Role    string `json:"role"`
			Content string `json:"content"`
		}{
			{Role: "user", Content: content},
		},
	}

	requestBody, err := json.Marshal(requestData)
	if err != nil {
		return fmt.Sprintf("请求体序列化失败: %v", err)
	}

	// 创建 HTTP 请求
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(requestBody))
	if err != nil {
		return fmt.Sprintf("创建请求失败: %v", err)
	}

	// 设置请求头
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	// 发送请求
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Sprintf("发送请求失败: %v", err)
	}
	defer resp.Body.Close()

	// 处理响应
	if resp.StatusCode == http.StatusOK {
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return fmt.Sprintf("读取响应失败: %v", err)
		}

		var responseData ResponseData
		err = json.Unmarshal(body, &responseData)
		if err != nil {
			return fmt.Sprintf("解析响应失败: %v", err)
		}

		if len(responseData.Choices) > 0 {
			ans := responseData.Choices[0].Message.Content
			GlobalCache.Set(content, ans)
			_ = GlobalCache.SavePer()
			return ans
		}
		return "未找到响应内容"
	}
	if resp.StatusCode == http.StatusTooManyRequests { // 429
		fmt.Println("请求过于频繁，等待重试...")
		retryAfter := 60 // 默认等待60秒
		if ra := resp.Header.Get("Retry-After"); ra != "" {
			if sec, err := strconv.Atoi(ra); err == nil {
				retryAfter = sec
			}
		}
		time.Sleep(time.Duration(retryAfter) * time.Second)
		return "" //askDeepSeek(prompt, text) // 递归重试
	}

	body, _ := io.ReadAll(resp.Body)
	return fmt.Sprintf("Error: %d - %s", resp.StatusCode, string(body))
}

// 计算两个集合的交集
func intersection(set1, set2 map[string]bool) map[string]bool {
	result := make(map[string]bool)
	for key := range set1 {
		if set2[key] {
			result[key] = true
		}
	}
	return result
}

// 计算两个集合的并集
func union(set1, set2 map[string]bool) map[string]bool {
	result := make(map[string]bool)
	for key := range set1 {
		result[key] = true
	}
	for key := range set2 {
		result[key] = true
	}
	return result
}

// 计算两个集合的差集（set1 - set2）
func difference(set1, set2 map[string]bool) map[string]bool {
	result := make(map[string]bool)
	for key := range set1 {
		if !set2[key] {
			result[key] = true
		}
	}
	return result
}

func ProcessArray[T any, R any](input []T, processFunc func(T) R) []R {
	var wg sync.WaitGroup
	output := make([]R, len(input))
	for i, val := range input {
		wg.Add(1)
		// 等待令牌
		if err := limiter.Wait(context.Background()); err != nil {
			log.Printf("限流等待失败: %v", err)
		}
		go func(index int, value T) {
			defer wg.Done()
			output[index] = processFunc(value)
		}(i, val)
	}

	wg.Wait()
	return output
}

func main() {
	NewProject("Project").Run()
	//fmt.Println(askDeepSeek("", "Hallo, wie geht es dir?"))
}
