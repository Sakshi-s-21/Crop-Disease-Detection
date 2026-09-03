document.addEventListener('DOMContentLoaded', () => {

    // =========================================================
    // ELEMENTS
    // =========================================================

    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('fileInput');
    const choosePhotoBtn = document.getElementById('choosePhotoBtn');
    const detectBtn = document.getElementById('detectBtn');

    const resultCard = document.getElementById('resultCard');

    const chatContainer = document.getElementById('chatContainer');
    const chatBody = document.getElementById('chatBody');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');

    let selectedFile = null;


    // =========================================================
    // CHOOSE PHOTO BUTTON
    // =========================================================

    if (choosePhotoBtn) {

        choosePhotoBtn.addEventListener('click', (e) => {

            e.stopPropagation();

            if (fileInput) {
                fileInput.click();
            }

        });

    }


    // =========================================================
    // UPLOAD AREA CLICK
    // =========================================================

    if (uploadArea) {

        uploadArea.addEventListener('click', (e) => {

            if (
                e.target !== choosePhotoBtn &&
                !e.target.classList.contains('preview')
            ) {

                if (fileInput) {
                    fileInput.click();
                }

            }

        });

    }


    // =========================================================
    // DRAG OVER
    // =========================================================

    if (uploadArea) {

        uploadArea.addEventListener('dragover', (e) => {

            e.preventDefault();

            uploadArea.classList.add('drag-over');

        });

    }


    // =========================================================
    // DRAG LEAVE
    // =========================================================

    if (uploadArea) {

        uploadArea.addEventListener('dragleave', () => {

            uploadArea.classList.remove('drag-over');

        });

    }


    // =========================================================
    // DROP
    // =========================================================

    if (uploadArea) {

        uploadArea.addEventListener('drop', (e) => {

            e.preventDefault();

            uploadArea.classList.remove('drag-over');

            if (e.dataTransfer.files.length > 0) {

                handleFile(e.dataTransfer.files[0]);

            }

        });

    }


    // =========================================================
    // FILE INPUT CHANGE
    // =========================================================

    if (fileInput) {

        fileInput.addEventListener('change', () => {

            if (fileInput.files.length > 0) {

                handleFile(fileInput.files[0]);

            }

        });

    }


    // =========================================================
    // HANDLE IMAGE FILE
    // =========================================================

    function handleFile(file) {

        if (!file.type.startsWith('image/')) {

            alert(
                'Please select an image file (JPG, PNG, WEBP)'
            );

            return;
        }


        selectedFile = file;


        // -----------------------------------------------------
        // Image preview
        // -----------------------------------------------------

        const reader = new FileReader();

        reader.onload = (e) => {

            const img = document.createElement('img');

            img.src = e.target.result;

            img.className = 'preview';

            img.style.maxWidth = '100%';
            img.style.marginTop = '15px';
            img.style.borderRadius = '8px';
            img.style.display = 'block';


            // Remove old preview
            const oldPreview =
                uploadArea.querySelector('img.preview');

            if (oldPreview) {

                oldPreview.remove();

            }


            uploadArea.appendChild(img);

            uploadArea.classList.add('preview-visible');

        };


        reader.readAsDataURL(file);


        // Enable detect button
        detectBtn.disabled = false;

    }


    // =========================================================
    // DETECT DISEASE
    // =========================================================

    if (detectBtn) {

        detectBtn.addEventListener('click', async () => {

            if (!selectedFile) {

                alert(
                    'Please select or drop a photo'
                );

                return;
            }


            detectBtn.disabled = true;

            detectBtn.textContent = 'Analyzing...';


            // -------------------------------------------------
            // Form data
            // -------------------------------------------------

            const formData = new FormData();

            formData.append(
                'file',
                selectedFile
            );


            try {

                const res = await fetch(
                    '/api/predict',
                    {
                        method: 'POST',
                        body: formData
                    }
                );


                const data = await res.json();


                // -------------------------------------------------
                // Error
                // -------------------------------------------------

                if (!res.ok || data.error) {

                    alert(
                        'Error: ' +
                        (data.error || 'Prediction failed')
                    );

                    return;
                }


                // =================================================
                // DISEASE NAME
                // =================================================

                const diseaseName =
                    document.getElementById('disease-name');

                if (diseaseName) {

                    diseaseName.textContent =
                        data.disease || 'Unknown disease';

                }


                // =================================================
                // CONFIDENCE
                // =================================================

                const confidence =
                    Number(data.confidence || 0);


                const confidenceText =
                    document.getElementById(
                        'confidence-text'
                    );

                if (confidenceText) {

                    confidenceText.textContent =
                        `${confidence.toFixed(2)}%`;

                }


                const confidenceBar =
                    document.getElementById(
                        'confidence-bar'
                    );

                if (confidenceBar) {

                    confidenceBar.style.width =
                        `${Math.min(confidence, 100)}%`;

                }


                // =================================================
                // EXPERT ADVICE
                // =================================================

                const adviceText =
                    document.getElementById(
                        'advice-text'
                    );


                if (adviceText) {

                    adviceText.innerHTML =
                        formatAdvice(
                            data.advice ||
                            'No expert advice available.'
                        );

                }


                // =================================================
                // RESULT IMAGE
                // =================================================

                const previewImg =
                    document.getElementById(
                        'preview-img'
                    );


                if (previewImg) {

                    let imageUrl =
                        data.image_url ||
                        data.image ||
                        '';


                    // If backend returns /uploads/...
                    // convert to /static/uploads/...
                    if (
                        imageUrl &&
                        imageUrl.startsWith('/uploads/')
                    ) {

                        imageUrl =
                            '/static' + imageUrl;

                    }


                    if (imageUrl) {

                        previewImg.src = imageUrl;

                        previewImg.style.display =
                            'block';

                    }

                }


                // =================================================
                // SHOW RESULT
                // =================================================

                if (resultCard) {

                    resultCard.style.display =
                        'block';

                }


                if (chatContainer) {

                    chatContainer.style.display =
                        'block';

                }


                // =================================================
                // INITIAL CHAT MESSAGE
                // =================================================

                addMessage(
                    'AI',
                    `Detected: ${data.disease} (${confidence.toFixed(2)}%). How can I help with treatment or prevention?`
                );

            }


            catch (err) {

                console.error(
                    'Prediction error:',
                    err
                );

                alert(
                    'Upload failed: ' +
                    err.message
                );

            }


            finally {

                detectBtn.disabled = false;

                detectBtn.textContent =
                    'Detect Disease';

            }

        });

    }


    // =========================================================
    // CHAT SEND BUTTON
    // =========================================================

    if (sendBtn) {

        sendBtn.addEventListener(
            'click',
            sendMessage
        );

    }


    // =========================================================
    // CHAT ENTER KEY
    // =========================================================

    if (chatInput) {

        chatInput.addEventListener(
            'keypress',
            (e) => {

                if (e.key === 'Enter') {

                    e.preventDefault();

                    sendMessage();

                }

            }
        );

    }


    // =========================================================
    // SEND CHAT MESSAGE
    // =========================================================

    function sendMessage() {

        const text =
            chatInput.value.trim();


        if (!text) {
            return;
        }


        // Show user message
        addMessage(
            'You',
            text
        );


        // Clear input
        chatInput.value = '';


        // Disable button
        sendBtn.disabled = true;


        // -----------------------------------------------------
        // Current disease
        // -----------------------------------------------------

        const diseaseElement =
            document.getElementById(
                'disease-name'
            );


        const disease =
            diseaseElement
                ? diseaseElement.textContent.trim()
                : '';


        // -----------------------------------------------------
        // Send to backend
        // -----------------------------------------------------

        fetch(
            '/api/chat',
            {
                method: 'POST',

                headers: {
                    'Content-Type':
                        'application/json'
                },

                body: JSON.stringify({

                    query: text,

                    disease: disease

                })
            }
        )


        // =====================================================
        // RESPONSE
        // =====================================================

        .then(async (res) => {

            const data =
                await res.json();


            if (!res.ok) {

                throw new Error(
                    data.error ||
                    'Server error'
                );

            }


            return data;

        })


        .then((data) => {

            addMessage(
                'AI',
                data.response ||
                'Sorry, could not get response.'
            );

        })


        .catch((err) => {

            console.error(
                'Chat error:',
                err
            );


            addMessage(
                'AI',
                'Sorry, there was an error connecting to the AI.'
            );

        })


        .finally(() => {

            sendBtn.disabled = false;

            chatInput.focus();

        });

    }


    // =========================================================
    // ESCAPE HTML
    // =========================================================

    function escapeHTML(text) {

        return String(text)

            .replace(
                /&/g,
                '&amp;'
            )

            .replace(
                /</g,
                '&lt;'
            )

            .replace(
                />/g,
                '&gt;'
            )

            .replace(
                /"/g,
                '&quot;'
            )

            .replace(
                /'/g,
                '&#039;'
            );
    }


    // =========================================================
    // FORMAT EXPERT ADVICE
    // =========================================================

    function formatAdvice(text) {

        if (!text) {

            return '<p>No expert advice available.</p>';

        }


        // -----------------------------------------------------
        // Convert to string
        // -----------------------------------------------------

        text = String(text);


        // -----------------------------------------------------
        // Normalize line breaks
        // -----------------------------------------------------

        text = text
            .replace(/\r\n/g, '\n')
            .replace(/\r/g, '\n');


        // -----------------------------------------------------
        // Escape HTML
        // -----------------------------------------------------

        text = escapeHTML(text);


        // =====================================================
        // REMOVE MARKDOWN HEADERS
        // =====================================================

        text = text.replace(
            /^#{1,6}\s*/gm,
            ''
        );


        // =====================================================
        // NORMALIZE BOLD MARKDOWN
        // =====================================================

        text = text.replace(
            /\*\*(.*?)\*\*/g,
            '%%BOLD%%$1%%ENDBOLD%%'
        );


        // =====================================================
        // CASE 1:
        // Proper bullet points already exist
        // =====================================================

        const hasBullets =
            /(^|\n)\s*[-•*]\s+/.test(text);


        // =====================================================
        // If proper bullets exist, use them
        // =====================================================

        if (hasBullets) {

            return formatExistingBullets(text);

        }


        // =====================================================
        // CASE 2:
        // AI sent bold headings inside one paragraph
        // =====================================================

        const parts =
            text.split('%%BOLD%%');


        let html = '';

        parts.forEach((part, index) => {

            if (index === 0) {

                html +=
                    formatNormalAdviceText(
                        part
                    );

                return;
            }


            const boldEnd =
                part.indexOf(
                    '%%ENDBOLD%%'
                );


            if (boldEnd === -1) {

                html +=
                    formatNormalAdviceText(
                        part
                    );

                return;

            }


            const heading =
                part
                    .substring(
                        0,
                        boldEnd
                    )
                    .trim();


            const remaining =
                part
                    .substring(
                        boldEnd +
                        '%%ENDBOLD%%'.length
                    )
                    .trim();


            // -------------------------------------------------
            // Heading
            // -------------------------------------------------

            html += `
                <div class="advice-heading">
                    ${heading}
                </div>
            `;


            // -------------------------------------------------
            // Text after heading
            // -------------------------------------------------

            if (remaining) {

                html +=
                    formatAdviceSection(
                        remaining
                    );

            }

        });


        return html;

    }


    // =========================================================
    // FORMAT EXISTING BULLETS
    // =========================================================

    function formatExistingBullets(text) {

        const lines =
            text.split('\n');


        let html = '';

        let inList = false;


        lines.forEach((line) => {

            const trimmed =
                line.trim();


            if (!trimmed) {

                if (inList) {

                    html += '</ul>';

                    inList = false;

                }

                return;

            }


            // -------------------------------------------------
            // Bold heading
            // -------------------------------------------------

            if (
                trimmed.includes('%%BOLD%%')
            ) {

                if (inList) {

                    html += '</ul>';

                    inList = false;

                }


                const heading =
                    trimmed
                        .replace(
                            /%%BOLD%%/g,
                            ''
                        )
                        .replace(
                            /%%ENDBOLD%%/g,
                            ''
                        );


                html += `
                    <div class="advice-heading">
                        ${heading}
                    </div>
                `;


                return;

            }


            // -------------------------------------------------
            // Bullet
            // -------------------------------------------------

            const bullet =
                trimmed.match(
                    /^[-•*]\s+(.*)$/
                );


            if (bullet) {

                if (!inList) {

                    html +=
                        '<ul class="advice-list">';

                    inList = true;

                }


                html +=
                    `<li>${formatInlineBold(
                        bullet[1]
                    )}</li>`;


                return;

            }


            // -------------------------------------------------
            // Numbered point
            // -------------------------------------------------

            const numbered =
                trimmed.match(
                    /^\d+[.)]\s+(.*)$/
                );


            if (numbered) {

                if (inList) {

                    html += '</ul>';

                    inList = false;

                }


                html += `
                    <div class="advice-number">
                        <strong>
                            ${trimmed.match(
                                /^\d+[.)]/
                            )[0]}
                        </strong>
                        ${formatInlineBold(
                            numbered[1]
                        )}
                    </div>
                `;


                return;

            }


            // -------------------------------------------------
            // Normal line
            // -------------------------------------------------

            if (inList) {

                html += '</ul>';

                inList = false;

            }


            html += `
                <p>
                    ${formatInlineBold(trimmed)}
                </p>
            `;

        });


        if (inList) {

            html += '</ul>';

        }


        return html;

    }


    // =========================================================
    // FORMAT ADVICE SECTION
    // =========================================================

    function formatAdviceSection(text) {

        // -----------------------------------------------------
        // First split by newline
        // -----------------------------------------------------

        let pieces =
            text.split('\n');


        // -----------------------------------------------------
        // If no newline, split long advice using semicolons
        // -----------------------------------------------------

        if (
            pieces.length === 1 &&
            text.includes(';')
        ) {

            pieces =
                text.split(';');

        }


        let html = '';

        let bulletItems = [];


        pieces.forEach((piece) => {

            const item =
                piece.trim();


            if (!item) {
                return;
            }


            // -------------------------------------------------
            // Existing bullet
            // -------------------------------------------------

            const bullet =
                item.match(
                    /^[-•*]\s+(.*)$/
                );


            if (bullet) {

                bulletItems.push(
                    bullet[1]
                );

                return;

            }


            // -------------------------------------------------
            // Numbered
            // -------------------------------------------------

            const numbered =
                item.match(
                    /^\d+[.)]\s+(.*)$/
                );


            if (numbered) {

                if (bulletItems.length) {

                    html += createBulletList(
                        bulletItems
                    );

                    bulletItems = [];

                }


                html += `
                    <div class="advice-number">
                        <strong>
                            ${item.match(
                                /^\d+[.)]/
                            )[0]}
                        </strong>
                        ${formatInlineBold(
                            numbered[1]
                        )}
                    </div>
                `;


                return;

            }


            // -------------------------------------------------
            // Normal text
            // -------------------------------------------------

            if (bulletItems.length) {

                html += createBulletList(
                    bulletItems
                );

                bulletItems = [];

            }


            html += `
                <ul class="advice-list">
                    <li>
                        ${formatInlineBold(item)}
                    </li>
                </ul>
            `;

        });


        if (bulletItems.length) {

            html += createBulletList(
                bulletItems
            );

        }


        return html;

    }


    // =========================================================
    // CREATE BULLET LIST
    // =========================================================

    function createBulletList(items) {

        let html =
            '<ul class="advice-list">';


        items.forEach((item) => {

            html += `
                <li>
                    ${formatInlineBold(item)}
                </li>
            `;

        });


        html += '</ul>';


        return html;

    }


    // =========================================================
    // FORMAT NORMAL ADVICE TEXT
    // =========================================================

    function formatNormalAdviceText(text) {

        if (!text) {
            return '';
        }


        text = text.trim();


        if (!text) {
            return '';
        }


        return `
            <p>
                ${formatInlineBold(text)}
            </p>
        `;

    }


    // =========================================================
    // INLINE BOLD
    // =========================================================

    function formatInlineBold(text) {

        return String(text).replace(
            /%%BOLD%%(.*?)%%ENDBOLD%%/g,
            '<strong>$1</strong>'
        );

    }


    // =========================================================
    // FORMAT CHAT RESPONSE
    // =========================================================

    function formatChatResponse(text) {

        if (!text) {

            return '';

        }


        text = escapeHTML(
            String(text)
        );


        // -----------------------------------------------------
        // Markdown bold
        // -----------------------------------------------------

        text = text.replace(
            /\*\*(.*?)\*\*/g,
            '%%BOLD%%$1%%ENDBOLD%%'
        );


        // -----------------------------------------------------
        // Markdown headings
        // -----------------------------------------------------

        text = text.replace(
            /^#{1,6}\s*(.*)$/gm,
            '%%HEADING%%$1%%ENDHEADING%%'
        );


        const lines =
            text.split('\n');


        let html = '';

        let inList = false;


        lines.forEach((line) => {

            const trimmed =
                line.trim();


            if (!trimmed) {

                if (inList) {

                    html += '</ul>';

                    inList = false;

                }

                return;

            }


            // -------------------------------------------------
            // Heading
            // -------------------------------------------------

            if (
                trimmed.includes(
                    '%%HEADING%%'
                )
            ) {

                if (inList) {

                    html += '</ul>';

                    inList = false;

                }


                const heading =
                    trimmed
                        .replace(
                            /%%HEADING%%/g,
                            ''
                        )
                        .replace(
                            /%%ENDHEADING%%/g,
                            ''
                        );


                html += `
                    <div class="chat-heading">
                        ${heading}
                    </div>
                `;


                return;

            }


            // -------------------------------------------------
            // Bullet
            // -------------------------------------------------

            const bullet =
                trimmed.match(
                    /^[-•*]\s+(.*)$/
                );


            if (bullet) {

                if (!inList) {

                    html +=
                        '<ul class="chat-list">';

                    inList = true;

                }


                html += `
                    <li>
                        ${formatInlineBold(
                            bullet[1]
                        )}
                    </li>
                `;


                return;

            }


            // -------------------------------------------------
            // Numbered
            // -------------------------------------------------

            const numbered =
                trimmed.match(
                    /^\d+[.)]\s+(.*)$/
                );


            if (numbered) {

                if (inList) {

                    html += '</ul>';

                    inList = false;

                }


                html += `
                    <div class="chat-numbered">
                        <strong>
                            ${trimmed.match(
                                /^\d+[.)]/
                            )[0]}
                        </strong>
                        ${formatInlineBold(
                            numbered[1]
                        )}
                    </div>
                `;


                return;

            }


            // -------------------------------------------------
            // Normal paragraph
            // -------------------------------------------------

            if (inList) {

                html += '</ul>';

                inList = false;

            }


            html += `
                <div class="chat-paragraph">
                    ${formatInlineBold(trimmed)}
                </div>
            `;

        });


        if (inList) {

            html += '</ul>';

        }


        return html;

    }


    // =========================================================
    // ADD CHAT MESSAGE
    // =========================================================

    function addMessage(sender, text) {

        const div =
            document.createElement('div');


        // -----------------------------------------------------
        // CSS class
        // -----------------------------------------------------

        div.className =
            sender === 'You'
                ? 'chat-message user-message'
                : 'chat-message ai-message';


        // -----------------------------------------------------
        // User message
        // -----------------------------------------------------

        if (sender === 'You') {

            div.textContent =
                text;

        }


        // -----------------------------------------------------
        // AI message
        // -----------------------------------------------------

        else {

            div.innerHTML =
                formatChatResponse(text);

        }


        // -----------------------------------------------------
        // Add message
        // -----------------------------------------------------

        chatBody.appendChild(div);


        // -----------------------------------------------------
        // Scroll
        // -----------------------------------------------------

        chatBody.scrollTop =
            chatBody.scrollHeight;

    }

});