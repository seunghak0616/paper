// Global variables
let allPapers = [];
let filteredPapers = [];
let currentPage = 1;
let itemsPerPage = 12;
let currentView = 'grid';
let currentPaper = null;

// API configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM elements
const elements = {
    searchInput: document.getElementById('searchInput'),
    searchBtn: document.getElementById('searchBtn'),
    statusFilter: document.getElementById('statusFilter'),
    yearFilter: document.getElementById('yearFilter'),
    sortBy: document.getElementById('sortBy'),
    resetBtn: document.getElementById('resetBtn'),
    papersContainer: document.getElementById('papersContainer'),
    loadingSpinner: document.getElementById('loadingSpinner'),
    emptyState: document.getElementById('emptyState'),
    gridViewBtn: document.getElementById('gridViewBtn'),
    listViewBtn: document.getElementById('listViewBtn'),
    prevBtn: document.getElementById('prevBtn'),
    nextBtn: document.getElementById('nextBtn'),
    pageNumbers: document.getElementById('pageNumbers'),
    paperModal: document.getElementById('paperModal'),
    closeModal: document.getElementById('closeModal'),
    modalTitle: document.getElementById('modalTitle'),
    totalCount: document.getElementById('totalCount'),
    successCount: document.getElementById('successCount'),
    failedCount: document.getElementById('failedCount'),
    avgQuality: document.getElementById('avgQuality'),
    toastContainer: document.getElementById('toastContainer')
};

// Event listeners
document.addEventListener('DOMContentLoaded', initializeApp);
elements.searchBtn.addEventListener('click', handleSearch);
elements.searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSearch();
});
elements.statusFilter.addEventListener('change', applyFilters);
elements.yearFilter.addEventListener('change', applyFilters);
elements.sortBy.addEventListener('change', applySorting);
elements.resetBtn.addEventListener('click', resetFilters);
elements.gridViewBtn.addEventListener('click', () => setView('grid'));
elements.listViewBtn.addEventListener('click', () => setView('list'));
elements.prevBtn.addEventListener('click', () => changePage(currentPage - 1));
elements.nextBtn.addEventListener('click', () => changePage(currentPage + 1));
elements.closeModal.addEventListener('click', closeModal);
elements.paperModal.addEventListener('click', (e) => {
    if (e.target === elements.paperModal) closeModal();
});

// Initialize application
async function initializeApp() {
    showLoading();
    try {
        await loadPapers();
        updateStatistics();
        applyFilters();
        setupYearFilter();
    } catch (error) {
        console.error('초기화 실패:', error);
        showToast('데이터 로드에 실패했습니다.', 'error');
        hideLoading();
    }
}

// Load papers from API or use mock data
async function loadPapers() {
    try {
        // Try to load from API first
        const response = await fetch(`${API_BASE_URL}/papers?limit=100`);
        if (response.ok) {
            const data = await response.json();
            allPapers = data.map(paper => ({
                id: paper.id,
                title: paper.title || '제목 없음',
                authors: paper.authors || '저자 정보 없음',
                publisher: paper.publisher || '발행기관 정보 없음',
                publication_year: paper.publication_year || '연도 정보 없음',
                keywords: paper.keywords || '',
                abstract: paper.abstract || '초록 정보 없음',
                abstractQuality: paper.abstract_quality_score || 0,
                extractionStatus: paper.text_extraction_status || 'failed',
                fullText: paper.full_text || '',
                textQuality: paper.text_quality_score || 0,
                pdfPath: paper.file_path || null,
                qualityScore: ((paper.abstract_quality_score || 0) + (paper.text_quality_score || 0)) / 2
            }));
            showToast('데이터를 성공적으로 로드했습니다.', 'success');
        } else {
            throw new Error('API 응답 오류');
        }
    } catch (error) {
        console.log('API 로드 실패, Mock 데이터 사용:', error);
        // Use mock data if API fails
        allPapers = getMockData();
        showToast('데모 데이터를 로드했습니다.', 'warning');
    }
}

// Mock data for development/testing
function getMockData() {
    return [
        {
            id: 'NODE10234568',
            title: 'AI 기반 스마트하우징 서비스를 위한 성능평가 요구사항에 관한 연구',
            authors: '김철수, 이영희, 박민수',
            publisher: '한국정보통신학회',
            publication_year: '2023',
            keywords: '인공지능, 스마트하우징, 성능평가, IoT',
            abstract: '본 연구는 AI 기반 스마트하우징 서비스의 성능평가를 위한 요구사항을 도출하고 분석하는 것을 목표로 한다. 최근 IoT 기술의 발전과 함께 스마트홈 환경에서의 AI 서비스가 급속히 증가하고 있으며, 이에 따른 성능평가의 중요성이 대두되고 있다. 본 연구에서는 문헌조사와 전문가 인터뷰를 통해 핵심 요구사항을 도출하였으며, 이를 바탕으로 성능평가 프레임워크를 제안하였다.',
            abstractQuality: 8.5,
            extractionStatus: 'success',
            fullText: '본 논문에서는 AI 기반 스마트하우징 서비스의 성능평가 요구사항에 대해 체계적으로 분석하였다. 연구 방법론으로는 문헌 조사와 전문가 인터뷰를 통해 핵심 요구사항을 도출하였으며, 이를 바탕으로 성능평가 프레임워크를 제안하였다. 제안된 프레임워크는 기능성, 성능, 사용성, 신뢰성 등의 측면에서 종합적인 평가가 가능하도록 설계되었다.',
            textQuality: 9.2,
            pdfPath: '/downloaded_pdfs/AI 기반 스마트하우징 서비스를 위한 성능평가 요구사항에 관한 연구.pdf',
            qualityScore: 8.85
        },
        {
            id: 'NODE10234569',
            title: '건설공사 관리분야에 있어서 Expert System의 이용에 관한 기초적 연구',
            authors: '정대한, 최영석',
            publisher: '대한건축학회',
            publication_year: '2022',
            keywords: '전문가시스템, 건설관리, 의사결정, 지식기반',
            abstract: '건설공사의 복잡성과 불확실성으로 인해 효율적인 관리가 어려운 상황에서, Expert System을 활용한 건설관리 방법론을 제안한다. 본 연구는 건설 프로젝트의 특성을 분석하고, 전문가 시스템의 적용 가능성을 탐구하였다.',
            abstractQuality: 7.8,
            extractionStatus: 'success',
            fullText: '건설 프로젝트는 다양한 이해관계자와 복잡한 프로세스를 포함하고 있어 체계적인 관리가 필요하다. 본 연구에서는 전문가 시스템을 활용하여 건설관리의 효율성을 높이는 방안을 제시하였다. 제안된 시스템은 의사결정 지원, 위험 관리, 자원 최적화 등의 기능을 포함한다.',
            textQuality: 8.1,
            pdfPath: '/downloaded_pdfs/건설공사 관리분야에 있어서 Expert System 의 이용에 관한 기초적 연구.pdf',
            qualityScore: 7.95
        },
        {
            id: 'NODE10234570',
            title: '인공지능 기법에 의한 건축설계 방법에 관한 연구',
            authors: '이준호, 김미영',
            publisher: '한국건축학회',
            publication_year: '2023',
            keywords: '인공지능, 건축설계, 생성모델, CAD',
            abstract: '본 연구는 AI 기법을 건축설계 프로세스에 적용하여 설계 효율성을 향상시키는 방법을 탐구한다. 머신러닝과 생성모델을 활용하여 건축 설계의 자동화 가능성을 검토하였다.',
            abstractQuality: 9.1,
            extractionStatus: 'failed',
            fullText: '',
            textQuality: 0,
            pdfPath: null,
            qualityScore: 4.55
        },
        {
            id: 'NODE10234571',
            title: '건축환경설비 분야의 인공지능 관련 최신 기술 및 연구동향',
            authors: '박지연, 김수민, 이동훈',
            publisher: '대한설비공학회',
            publication_year: '2023',
            keywords: '인공지능, 건축환경설비, HVAC, 에너지효율',
            abstract: '건축환경설비 분야에서의 인공지능 기술 적용 현황과 최신 연구동향을 분석하였다. HVAC 시스템의 최적화, 에너지 효율성 향상, 실내환경 제어 등의 분야에서 AI 기술의 활용 사례를 조사하였다.',
            abstractQuality: 8.7,
            extractionStatus: 'success',
            fullText: '건축환경설비 분야는 에너지 효율성과 실내환경 쾌적성을 동시에 추구해야 하는 복잡한 영역이다. 본 연구에서는 AI 기술을 활용한 스마트 빌딩 시스템의 최신 동향을 분석하였으며, 머신러닝 기반의 예측 제어, 강화학습을 활용한 최적화 등의 기술을 검토하였다.',
            textQuality: 8.9,
            pdfPath: '/downloaded_pdfs/건축환경설비 분야의 인공지능 관련 최신 기술 및 연구동향.pdf',
            qualityScore: 8.8
        },
        {
            id: 'NODE10234572',
            title: '지식 보조디자인 시스템의 개발에 관한 연구',
            authors: '황준호, 서미경',
            publisher: '한국디자인학회',
            publication_year: '2021',
            keywords: '지식기반시스템, 디자인지원, CAD, 전문가시스템',
            abstract: '설계 과정에서의 지식 활용을 체계화하고 디자이너의 의사결정을 지원하는 지식 보조디자인 시스템의 개발에 관한 연구를 수행하였다. 전문가의 설계 지식을 체계화하고 이를 시스템에 반영하는 방법론을 제시하였다.',
            abstractQuality: 7.5,
            extractionStatus: 'success',
            fullText: '설계 과정은 복잡한 의사결정의 연속이며, 전문가의 경험과 지식이 중요한 역할을 한다. 본 연구에서는 이러한 설계 지식을 체계화하고 컴퓨터 시스템을 통해 활용할 수 있는 방안을 제시하였다. 제안된 시스템은 규칙기반 추론과 사례기반 추론을 결합한 하이브리드 접근법을 채택하였다.',
            textQuality: 7.8,
            pdfPath: '/downloaded_pdfs/지식 보조디자인 시스템의 개발에 관한 연구 (1).pdf',
            qualityScore: 7.65
        },
        {
            id: 'NODE10234573',
            title: '스마트시티 구현을 위한 IoT 기반 통합관리시스템 연구',
            authors: '최민철, 정소영',
            publisher: '한국정보과학회',
            publication_year: '2022',
            keywords: 'IoT, 스마트시티, 통합관리, 빅데이터',
            abstract: '스마트시티 구현을 위한 IoT 기반 통합관리시스템의 설계 및 구현에 관한 연구를 수행하였다. 다양한 도시 인프라에서 수집되는 데이터를 통합 관리하고 분석하는 플랫폼을 제안하였다.',
            abstractQuality: 8.2,
            extractionStatus: 'failed',
            fullText: '',
            textQuality: 0,
            pdfPath: null,
            qualityScore: 4.1
        }
    ];
}

// Update statistics
function updateStatistics() {
    const total = allPapers.length;
    const success = allPapers.filter(p => p.extractionStatus === 'success').length;
    const failed = total - success;
    const avgQuality = success > 0 ? 
        (allPapers.filter(p => p.extractionStatus === 'success')
            .reduce((sum, p) => sum + p.qualityScore, 0) / success).toFixed(1) : '0.0';

    elements.totalCount.textContent = total;
    elements.successCount.textContent = success;
    elements.failedCount.textContent = failed;
    elements.avgQuality.textContent = avgQuality;
}

// Setup year filter options
function setupYearFilter() {
    const years = [...new Set(allPapers.map(p => p.publication_year))].sort().reverse();
    elements.yearFilter.innerHTML = '<option value="all">전체</option>';
    years.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        elements.yearFilter.appendChild(option);
    });
}

// Handle search
function handleSearch() {
    applyFilters();
}

// Apply filters
function applyFilters() {
    const searchTerm = elements.searchInput.value.toLowerCase().trim();
    const statusFilter = elements.statusFilter.value;
    const yearFilter = elements.yearFilter.value;

    filteredPapers = allPapers.filter(paper => {
        const matchesSearch = !searchTerm || 
            paper.title.toLowerCase().includes(searchTerm) ||
            paper.authors.toLowerCase().includes(searchTerm) ||
            paper.keywords.toLowerCase().includes(searchTerm);
        
        const matchesStatus = statusFilter === 'all' || paper.extractionStatus === statusFilter;
        const matchesYear = yearFilter === 'all' || paper.publication_year === yearFilter;

        return matchesSearch && matchesStatus && matchesYear;
    });

    applySorting();
}

// Apply sorting
function applySorting() {
    const sortBy = elements.sortBy.value;
    
    filteredPapers.sort((a, b) => {
        switch (sortBy) {
            case 'title':
                return a.title.localeCompare(b.title);
            case 'year':
                return b.publication_year.localeCompare(a.publication_year);
            case 'quality':
                return b.qualityScore - a.qualityScore;
            default:
                return 0;
        }
    });

    currentPage = 1;
    renderPapers();
    updatePagination();
}

// Reset filters
function resetFilters() {
    elements.searchInput.value = '';
    elements.statusFilter.value = 'all';
    elements.yearFilter.value = 'all';
    elements.sortBy.value = 'title';
    filteredPapers = [...allPapers];
    applySorting();
}

// Set view mode
function setView(view) {
    currentView = view;
    elements.gridViewBtn.classList.toggle('active', view === 'grid');
    elements.listViewBtn.classList.toggle('active', view === 'list');
    elements.papersContainer.className = `papers-container ${view}-view`;
    renderPapers();
}

// Render papers
function renderPapers() {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const papersToShow = filteredPapers.slice(startIndex, endIndex);

    if (papersToShow.length === 0) {
        elements.papersContainer.innerHTML = '';
        elements.emptyState.style.display = 'block';
        hideLoading();
        return;
    }

    elements.emptyState.style.display = 'none';
    elements.papersContainer.innerHTML = papersToShow.map(paper => createPaperCard(paper)).join('');
    hideLoading();

    // Add click listeners to paper cards
    document.querySelectorAll('.paper-card').forEach((card, index) => {
        card.addEventListener('click', () => showPaperDetails(papersToShow[index]));
    });
}

// Create paper card HTML
function createPaperCard(paper) {
    const keywords = paper.keywords.split(',').map(k => k.trim()).filter(k => k);
    const keywordTags = keywords.slice(0, 5).map(keyword => 
        `<span class="keyword-tag">${keyword}</span>`
    ).join('');

    const statusIcon = paper.extractionStatus === 'success' ? 
        '<i class="fas fa-check-circle"></i>' : 
        '<i class="fas fa-times-circle"></i>';

    return `
        <div class="paper-card ${paper.extractionStatus}" data-id="${paper.id}">
            <div class="paper-status ${paper.extractionStatus}">
                ${statusIcon}
            </div>
            <div class="paper-info">
                <h3 class="paper-title">${paper.title}</h3>
                <div class="paper-meta">
                    <span><i class="fas fa-user"></i> ${paper.authors}</span>
                    <span><i class="fas fa-building"></i> ${paper.publisher}</span>
                    <span><i class="fas fa-calendar"></i> ${paper.publication_year}</span>
                </div>
                <div class="paper-keywords">
                    ${keywordTags}
                </div>
                <div class="paper-quality">
                    <span class="quality-score">
                        <i class="fas fa-star"></i>
                        ${paper.qualityScore.toFixed(1)}
                    </span>
                    <span class="extraction-status">
                        ${paper.extractionStatus === 'success' ? '추출 완료' : '추출 실패'}
                    </span>
                </div>
            </div>
        </div>
    `;
}

// Show paper details in modal
function showPaperDetails(paper) {
    currentPaper = paper; // Store current paper for PDF functions
    elements.modalTitle.textContent = paper.title;
    
    const modalBody = document.querySelector('.modal-body .paper-details');
    modalBody.innerHTML = `
        <div class="detail-grid">
            <div class="detail-item">
                <strong>논문 ID</strong>
                <span>${paper.id}</span>
            </div>
            <div class="detail-item">
                <strong>저자</strong>
                <span>${paper.authors}</span>
            </div>
            <div class="detail-item">
                <strong>발행기관</strong>
                <span>${paper.publisher}</span>
            </div>
            <div class="detail-item">
                <strong>발행년도</strong>
                <span>${paper.publication_year}</span>
            </div>
            <div class="detail-item">
                <strong>추출 상태</strong>
                <span class="${paper.extractionStatus}">
                    ${paper.extractionStatus === 'success' ? '성공' : '실패'}
                </span>
            </div>
            <div class="detail-item">
                <strong>품질 점수</strong>
                <span>${paper.qualityScore.toFixed(1)} / 10.0</span>
            </div>
        </div>
        
        <div class="detail-section">
            <h3>키워드</h3>
            <div class="paper-keywords">
                ${paper.keywords.split(',').map(k => k.trim()).filter(k => k).map(keyword => 
                    `<span class="keyword-tag">${keyword}</span>`
                ).join('')}
            </div>
        </div>
        
        <div class="detail-section">
            <h3>초록</h3>
            <p>${paper.abstract}</p>
        </div>
        
        ${paper.fullText ? `
            <div class="detail-section">
                <h3>추출된 원문 (일부)</h3>
                <p>${paper.fullText.substring(0, 500)}${paper.fullText.length > 500 ? '...' : ''}</p>
            </div>
        ` : ''}
        
        <div class="detail-section">
            <h3>품질 세부 정보</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <strong>초록 품질</strong>
                    <span>${paper.abstractQuality.toFixed(1)} / 10.0</span>
                </div>
                <div class="detail-item">
                    <strong>원문 품질</strong>
                    <span>${paper.textQuality.toFixed(1)} / 10.0</span>
                </div>
            </div>
        </div>
    `;
    
    // Update button states
    const previewBtn = document.getElementById('previewPdfBtn');
    const downloadBtn = document.getElementById('downloadPdfBtn');
    
    if (paper.pdfPath && paper.extractionStatus === 'success') {
        previewBtn.disabled = false;
        downloadBtn.disabled = false;
    } else {
        previewBtn.disabled = true;
        downloadBtn.disabled = true;
    }
    
    elements.paperModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Close modal
function closeModal() {
    elements.paperModal.classList.remove('active');
    document.body.style.overflow = 'auto';
    currentPaper = null;
}

// PDF Preview Functions
function previewPdf() {
    if (!currentPaper || !currentPaper.pdfPath) {
        showToast('PDF 파일을 찾을 수 없습니다.', 'error');
        return;
    }
    
    const pdfModal = document.getElementById('pdfModal');
    const pdfModalTitle = document.getElementById('pdfModalTitle');
    const pdfViewer = document.getElementById('pdfViewer');
    const pdfLoadingSpinner = document.getElementById('pdfLoadingSpinner');
    const pdfError = document.getElementById('pdfError');
    
    // Set modal title
    pdfModalTitle.textContent = `PDF 미리보기: ${currentPaper.title}`;
    
    // Show modal and loading
    pdfModal.classList.add('active');
    pdfLoadingSpinner.style.display = 'block';
    pdfViewer.style.display = 'none';
    pdfError.style.display = 'none';
    
    // For demo purposes, create a mock PDF URL
    // In real implementation, this would use the actual PDF path
    const pdfUrl = createMockPdfUrl(currentPaper);
    
    // Create iframe for PDF viewing
    const iframe = document.createElement('iframe');
    iframe.src = pdfUrl;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = 'none';
    
    // Handle load events
    iframe.onload = function() {
        pdfLoadingSpinner.style.display = 'none';
        pdfViewer.style.display = 'block';
        showToast('PDF 로드 완료', 'success');
    };
    
    iframe.onerror = function() {
        pdfLoadingSpinner.style.display = 'none';
        pdfError.style.display = 'block';
        showToast('PDF 로드 실패', 'error');
    };
    
    // Clear previous content and add iframe
    pdfViewer.innerHTML = '';
    pdfViewer.appendChild(iframe);
    
    // Fallback timeout
    setTimeout(() => {
        if (pdfLoadingSpinner.style.display !== 'none') {
            pdfLoadingSpinner.style.display = 'none';
            pdfError.style.display = 'block';
        }
    }, 10000);
}

function closePdfModal() {
    const pdfModal = document.getElementById('pdfModal');
    const pdfViewer = document.getElementById('pdfViewer');
    
    pdfModal.classList.remove('active');
    pdfViewer.innerHTML = ''; // Clear iframe to stop loading
}

function downloadPdf() {
    if (!currentPaper || !currentPaper.pdfPath) {
        showToast('PDF 파일을 찾을 수 없습니다.', 'error');
        return;
    }
    
    showToast('PDF 다운로드를 시작합니다...', 'info');
    
    try {
        // For demo purposes, create a mock download
        // In real implementation, this would download the actual PDF
        const pdfUrl = createMockPdfUrl(currentPaper);
        const link = document.createElement('a');
        link.href = pdfUrl;
        link.download = `${currentPaper.title}.pdf`;
        link.target = '_blank';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showToast('PDF 다운로드 완료!', 'success');
    } catch (error) {
        console.error('PDF 다운로드 오류:', error);
        showToast('PDF 다운로드 중 오류가 발생했습니다.', 'error');
    }
}

function createMockPdfUrl(paper) {
    // For demo purposes, create a data URL with PDF-like content
    // In real implementation, this would be the actual PDF file URL
    if (paper.extractionStatus === 'success') {
        // Use PDF.js viewer with a sample PDF or create a simple PDF
        return `data:application/pdf;base64,JVBERi0xLjcKCjEgMCBvYmogICUgZW50cnkgcG9pbnQKPDwKL1R5cGUgL0NhdGFsb2cKL1BhZ2VzIDIgMCBSCj4+CmVuZG9iagoKMiAwIG9iagpbXSBvYmogICUgcGFnZSBvYmplY3QKPDwKL1R5cGUgL1BhZ2VzCi9LaWRzIFszIDAgUl0KL0NvdW50IDEKL01lZGlhQm94IFswIDAgMzAwIDQ0Ml0KPj4KZW5kb2JqCgozIDAgb2JqCjw8Ci9UeXBlIC9QYWdlCi9QYXJlbnQgMiAwIFIKL1Jlc291cmNlcyA8PAovRm9udCA8PAovRjEgNCAwIFIKPj4KPj4KL0NvbnRlbnRzIDUgMCBSCj4+CmVuZG9iagoKNCAwIG9iago8PAovVHlwZSAvRm9udAovU3VidHlwZSAvVHlwZTEKL0Jhc2VGb250IC9UaW1lcy1Sb21hbgo+PgplbmRvYmoKCjUgMCBvYmoKPDwKL0xlbmd0aCAyNgogMzI+PgpzdHJlYW0KQlQKL0YxIDEyIFRmCjcyIDcwOCBUZApIZWxsbyBXb3JsZCEpJwpFVApmdW5kYm9qZW1lZiBiCgplbmRzdHJlYW0KZW5kb2JqCgp4cmVmCjAgNgo8PDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwOSAwMDAwMCBuIAowMDAwMDAwNzQgMDAwMDAgbiAKMDAwMDAwMTc5IDAwMDAwIG4gCjAwMDAwMDMxNCAwMDAwMCBuIAowMDAwMDAzOTUgMDAwMDAgbiAKdHJhaWxlcgo8PAovU2l6ZSA2Ci9Sb290IDEgMCBSCj4+CnN0YXJ0eHJlZgo1NTYKJSVFT0YK`;
    } else {
        return null;
    }
}

// Pagination
function updatePagination() {
    const totalPages = Math.ceil(filteredPapers.length / itemsPerPage);
    
    elements.prevBtn.disabled = currentPage === 1;
    elements.nextBtn.disabled = currentPage === totalPages || totalPages === 0;
    
    // Update page numbers
    elements.pageNumbers.innerHTML = '';
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `page-number ${i === currentPage ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.addEventListener('click', () => changePage(i));
        elements.pageNumbers.appendChild(pageBtn);
    }
}

// Change page
function changePage(page) {
    const totalPages = Math.ceil(filteredPapers.length / itemsPerPage);
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        renderPapers();
        updatePagination();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Show loading
function showLoading() {
    elements.loadingSpinner.style.display = 'block';
    elements.emptyState.style.display = 'none';
}

// Hide loading
function hideLoading() {
    elements.loadingSpinner.style.display = 'none';
}

// Show toast notification
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, duration);
}

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);