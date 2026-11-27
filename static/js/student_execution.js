"use strict";

class StudentExecutionController {

    constructor(assignmentId) {

        if (
            typeof assignmentId !== "string" ||
            !assignmentId.trim()
        ) {

            throw new Error(
                "Geçersiz etkinlik ataması."
            );
        }

        this.assignmentId = assignmentId;

        this.performanceSessionId = null;

        this.execution = null;

        this.assignment = null;

        this.busy = false;

        this.pendingResponse = null;

        this.reconciliationRequired = false;

        this.staleStoredResponse = null;
    }


    get endpoint() {

        return (
            "/api/student-execution/" +
            encodeURIComponent(this.assignmentId)
        );
    }


    get currentQuestion() {

        return this.execution?.question || null;
    }


    get canSubmitResponse() {

        return (
            !this.busy &&
            !this.reconciliationRequired &&
            this.pendingResponse === null &&
            this.execution?.allowed_operations
                ?.submit_response === true
        );
    }


    get canStartRepetition() {

        return (
            !this.busy &&
            !this.reconciliationRequired &&
            this.pendingResponse === null &&
            this.execution?.allowed_operations
                ?.start_repetition === true
        );
    }


    get canCompleteAssignment() {

        return (
            !this.busy &&
            !this.reconciliationRequired &&
            this.pendingResponse === null &&
            this.execution?.allowed_operations
                ?.complete_assignment === true
        );
    }


    async apiRequest(
        url,
        method = "GET",
        payload = null
    ) {

        const options = {

            method,

            cache: "no-store",

            credentials: "same-origin"
        };

        if (payload !== null) {

            options.headers = {
                "Content-Type": "application/json"
            };

            options.body = JSON.stringify(payload);
        }

        const response = await fetch(
            url,
            options
        );

        let result;

        try {

            result = await response.json();

        } catch (error) {

            throw new Error(
                "Sunucudan geçerli cevap alınamadı."
            );
        }

        if (
            !response.ok ||
            result?.ok !== true
        ) {

            const error = new Error(
                result?.error ||
                "İşlem gerçekleştirilemedi."
            );

            error.httpStatus = response.status;

            throw error;
        }

        return result;
    }


    applyExecutionState(result) {

        if (
            result.assignment?.assignment_id
            !== this.assignmentId
        ) {

            throw new Error(
                "Etkinlik ataması uyuşmuyor."
            );
        }

        if (
            typeof result.performance_session_id
                !== "string" ||

            !result.performance_session_id.trim()
        ) {

            throw new Error(
                "Geçerli performans oturumu bulunamadı."
            );
        }

        if (
            this.performanceSessionId !== null &&

            this.performanceSessionId
                !== result.performance_session_id
        ) {

            throw new Error(
                "Öğrenme oturumu değişmiş. " +
                "Öğrenci paneline dönünüz."
            );
        }

        const execution = result.execution;

        const question = execution?.question;

        const expectedRoundStatuses = {

            AWAITING_RESPONSE: "ACTIVE",

            REPEAT_REQUIRED: "REPEAT_REQUIRED",

            SUCCESS_CONFIRMED: "SUCCESS_CONFIRMED"
        };

        if (
            !execution ||

            !Object.prototype.hasOwnProperty.call(
                expectedRoundStatuses,
                execution.status
            ) ||

            !question ||

            typeof question.question_id !== "string" ||

            !question.question_id.trim() ||

            !Number.isInteger(question.round_number) ||

            question.round_number < 1 ||

            question.round_number
                !== execution.round_number ||

            question.status
                !== expectedRoundStatuses[
                    execution.status
                ] ||

            !question.presentation ||

            !Array.isArray(
                question.presentation.presented_choices
            ) ||

            question.presentation.presented_choices.length < 2 ||

            !execution.allowed_operations
        ) {

            throw new Error(
                "Etkinlik durumu geçerli değil."
            );
        }

        this.assignment = result.assignment;

        this.performanceSessionId =
            result.performance_session_id;

        this.execution = execution;
    }


    get pendingResponseStorageKey() {

        return (
            "personalized-learning:pending-response:v1:" +
            this.assignmentId
        );
    }


    persistPendingResponse() {

        if (!this.pendingResponse) {

            throw new Error(
                "Saklanacak cevap bulunmuyor."
            );
        }

        try {

            sessionStorage.setItem(

                this.pendingResponseStorageKey,

                JSON.stringify(
                    this.pendingResponse
                )
            );

        } catch (error) {

            throw new Error(
                "Cevap güvenli biçimde saklanamadı. " +
                "Öğretmeninize danışınız."
            );
        }
    }


    readStoredPendingResponse() {

        const raw = sessionStorage.getItem(
            this.pendingResponseStorageKey
        );

        if (raw === null) {

            return null;
        }

        const payload = JSON.parse(raw);

        if (
            !payload ||

            typeof payload.performance_session_id
                !== "string" ||

            !payload.performance_session_id.trim() ||

            typeof payload.question_id !== "string" ||

            !payload.question_id.trim() ||

            typeof payload.request_id !== "string" ||

            !payload.request_id.trim() ||

            !Number.isInteger(
                payload.selected_position
            ) ||

            payload.selected_position < 0
        ) {

            throw new Error(
                "Saklanan cevap bilgisi geçersiz."
            );
        }

        return Object.freeze({

            performance_session_id:
                payload.performance_session_id,

            question_id:
                payload.question_id,

            request_id:
                payload.request_id,

            selected_position:
                payload.selected_position
        });
    }


    restorePendingResponse() {

        if (!this.performanceSessionId) {

            throw new Error(
                "Öğrenme oturumu doğrulanamadı."
            );
        }

        const stored =
            this.readStoredPendingResponse();

        this.restoreResponseConflict(stored);

        this.staleStoredResponse = null;

        this.responseConflict = null;

        if (stored === null) {

            if (this.pendingResponse !== null) {

                throw new Error(
                    "Bekleyen cevap kaydı bulunamadı."
                );
            }

            return "NO_PENDING_RESPONSE";
        }

        if (
            stored.performance_session_id
                !== this.performanceSessionId
        ) {

            this.staleStoredResponse = stored;

            this.reconciliationRequired = true;

            return "STALE_PERFORMANCE_SESSION";
        }

        if (this.pendingResponse !== null) {

            const current = this.pendingResponse;

            if (
                current.performance_session_id
                    !== stored.performance_session_id ||

                current.question_id
                    !== stored.question_id ||

                current.request_id
                    !== stored.request_id ||

                current.selected_position
                    !== stored.selected_position
            ) {

                throw new Error(
                    "Bekleyen cevap bilgileri uyuşmuyor."
                );
            }
        }

        this.pendingResponse = stored;

        this.reconciliationRequired = true;

        return "PENDING_RESPONSE_RESTORED";
    }


    get hasStaleStoredResponse() {

        return this.staleStoredResponse !== null;
    }


    clearStoredPendingResponse() {

        sessionStorage.removeItem(
            this.pendingResponseStorageKey
        );
    }


    createRequestId() {

        if (typeof crypto.randomUUID === "function") {

            return crypto.randomUUID();
        }

        const bytes = crypto.getRandomValues(
            new Uint8Array(16)
        );

        bytes[6] = (bytes[6] & 15) | 64;

        bytes[8] = (bytes[8] & 63) | 128;

        const hex = Array.from(
            bytes,
            value => value.toString(16).padStart(2, "0")
        ).join("");

        return [
            hex.slice(0, 8),
            hex.slice(8, 12),
            hex.slice(12, 16),
            hex.slice(16, 20),
            hex.slice(20)
        ].join("-");
    }


    async submitResponse(selectedPosition) {

        if (!this.canSubmitResponse) {

            throw new Error(
                "Şu anda cevap gönderilemez."
            );
        }

        const question = this.currentQuestion;

        const choices =
            question.presentation.presented_choices;

        if (
            !Number.isInteger(selectedPosition) ||
            selectedPosition < 0 ||
            selectedPosition >= choices.length
        ) {

            throw new Error(
                "Geçersiz cevap seçimi."
            );
        }

        this.pendingResponse = Object.freeze({

            performance_session_id:
                this.performanceSessionId,

            question_id:
                question.question_id,

            request_id:
                this.createRequestId(),

            selected_position:
                selectedPosition
        });

        try {

            this.persistPendingResponse();

        } catch (error) {

            this.pendingResponse = null;

            throw error;
        }

        return this.sendPendingResponse();
    }


    validateResponseAcknowledgement(result, payload) {

        if (
            result.assignment_id !== this.assignmentId ||

            result.performance_session_id
                !== payload.performance_session_id ||

            result.question_id !== payload.question_id ||

            result.request_id !== payload.request_id ||

            result.response_event_id !== payload.request_id ||

            result.attempt?.selected_position
                !== payload.selected_position ||

            typeof result.duplicate_request !== "boolean"
        ) {

            throw new Error(
                "Cevap doğrulama bilgileri uyuşmuyor."
            );
        }

        const feedbackTypes = [

            "SUCCESS",

            "ENCOURAGEMENT",

            "DISCOVERY"
        ];

        const nextActions = [

            "CONTINUE",

            "REPEAT",

            "AUTHORIZE_COMPLETION"
        ];

        if (
            !feedbackTypes.includes(
                result.feedback?.type
            ) ||

            !nextActions.includes(
                result.progression?.next_action
            ) ||

            !Number.isInteger(
                result.attempt?.attempt_number
            ) ||

            result.attempt.attempt_number < 1
        ) {

            throw new Error(
                "Sunucu cevap değerlendirmesi geçersiz."
            );
        }
    }


    validateResponseInspection(result, payload) {

        if (
            result.assignment_id !== this.assignmentId ||

            result.performance_session_id
                !== payload.performance_session_id ||

            result.question_id !== payload.question_id ||

            result.request_id !== payload.request_id ||

            result.selected_position
                !== payload.selected_position
        ) {

            throw new Error(
                "Cevap kontrol bilgileri uyuşmuyor."
            );
        }

        const allowedRecordingStatuses = [

            "RECORDED",

            "NOT_RECORDED",

            "CONFLICT"
        ];

        if (
            !allowedRecordingStatuses.includes(
                result.recording_status
            )
        ) {

            throw new Error(
                "Geçersiz cevap kayıt durumu."
            );
        }

        const allowedSessionStatuses = [

            "ACTIVE",

            "COMPLETED",

            "TERMINATED",

            "INTERRUPTED"
        ];

        if (
            !allowedSessionStatuses.includes(
                result.session_status
            )
        ) {

            throw new Error(
                "Geçersiz öğrenme oturumu durumu."
            );
        }

        if (result.recording_status === "RECORDED") {

            const recorded =
                result.recorded_response;

            if (
                !recorded ||

                recorded.event_id !== payload.request_id ||

                typeof recorded.attempt_id !== "string" ||

                !recorded.attempt_id.trim() ||

                !Number.isInteger(
                    recorded.sequence_number
                ) ||

                recorded.sequence_number < 1 ||

                !Number.isInteger(
                    recorded.attempt_number
                ) ||

                recorded.attempt_number < 1 ||

                typeof recorded.recorded_at !== "string" ||

                !Number.isFinite(
                    Date.parse(recorded.recorded_at)
                )
            ) {

                throw new Error(
                    "Kaydedilen cevap doğrulanamadı."
                );
            }
        }
    }


    async completeAssignment() {

        if (!this.canCompleteAssignment) {
            return;
        }

        this.busy = true;

        try {

            const result = await this.apiRequest(
                this.endpoint + "/complete",
                "POST",
                {
                    performance_session_id:
                        this.performanceSessionId
                }
            );

            if (
                result.assignment_id !== this.assignmentId ||
                result.performance_session_id !==
                    this.performanceSessionId ||
                result.assignment_status !== "COMPLETED" ||
                result.execution_status !== "COMPLETED"
            ) {
                throw new Error(
                    "Etkinlik tamamlanması doğrulanamadı."
                );
            }

            return result;

        } catch (error) {

            this.reconciliationRequired = true;

            throw error;

        } finally {

            this.busy = false;
        }
    }


    async startRepetition() {

        if (!this.canStartRepetition) {
            return;
        }

        const previousQuestionId =
            this.currentQuestion.question_id;

        this.busy = true;

        try {

            await this.apiRequest(
                this.endpoint + "/repeat",
                "POST",
                {
                    performance_session_id:
                        this.performanceSessionId,

                    previous_question_id:
                        previousQuestionId
                }
            );

            const latest = await this.apiRequest(
                this.endpoint
            );

            this.applyExecutionState(latest);

            this.reconciliationRequired = false;

        } catch (error) {

            this.reconciliationRequired = true;

            throw error;

        } finally {

            this.busy = false;
        }
    }


    async inspectPendingResponse() {

        if (this.busy) {

            throw new Error(
                "Devam eden bir işlem bulunuyor."
            );
        }

        const payload =
            this.staleStoredResponse ||
            this.pendingResponse;

        if (!payload) {

            throw new Error(
                "Kontrol edilecek cevap bulunmuyor."
            );
        }

        this.busy = true;

        this.reconciliationRequired = true;

        try {

            const result = await this.apiRequest(

                this.endpoint + "/response-status",

                "POST",

                payload
            );

            this.validateResponseInspection(
                result,
                payload
            );

            return result;

        } finally {

            this.busy = false;
        }
    }


    async resolveRecordedResponse() {

        if (this.busy) {

            throw new Error(
                "Devam eden bir işlem bulunuyor."
            );
        }

        const payload =
            this.staleStoredResponse ||
            this.pendingResponse;

        if (!payload) {

            throw new Error(
                "Çözümlenecek cevap kaydı bulunmuyor."
            );
        }

        this.busy = true;

        this.reconciliationRequired = true;

        try {

            // Obtain fresh authoritative confirmation.
            // Do not rely on an earlier inspection result.

            const inspection = await this.apiRequest(

                this.endpoint + "/response-status",

                "POST",

                payload
            );

            this.validateResponseInspection(
                inspection,
                payload
            );

            if (
                inspection.recording_status
                    !== "RECORDED"
            ) {

                throw new Error(
                    "Cevabın kaydedildiği doğrulanamadı."
                );
            }

            // Retrieve the current execution state before
            // removing any local recovery information.

            const latest = await this.apiRequest(
                this.endpoint
            );

            this.applyExecutionState(latest);

            // Confirm that browser storage still contains
            // the exact response being resolved.

            const stored =
                this.readStoredPendingResponse();

            if (
                !stored ||

                stored.request_id
                    !== payload.request_id ||

                stored.performance_session_id
                    !== payload.performance_session_id ||

                stored.question_id
                    !== payload.question_id ||

                stored.selected_position
                    !== payload.selected_position
            ) {

                throw new Error(
                    "Bekleyen cevap bilgisi değişmiş."
                );
            }

            // Remove conflict information first.
            // If pending response cleanup fails,
            // the original response remains recoverable.

            this.clearStoredResponseConflict();

            this.clearStoredPendingResponse();

            this.pendingResponse = null;

            this.staleStoredResponse = null;

            this.reconciliationRequired = false;

            return {

                resolved: true,

                recording_status: "RECORDED",

                request_id: payload.request_id,

                recorded_response:
                    inspection.recorded_response,

                execution: this.execution
            };

        } catch (error) {

            this.reconciliationRequired = true;

            throw error;

        } finally {

            this.busy = false;
        }
    }


    get responseConflictStorageKey() {

        return (
            "personalized-learning:response-conflict:v1:" +
            this.assignmentId
        );
    }


    persistResponseConflict() {

        if (!this.responseConflict) {

            throw new Error(
                "Saklanacak cevap uyuşmazlığı bulunmuyor."
            );
        }

        sessionStorage.setItem(

            this.responseConflictStorageKey,

            JSON.stringify(
                this.responseConflict
            )
        );
    }


    restoreResponseConflict(payload) {

        const raw = sessionStorage.getItem(
            this.responseConflictStorageKey
        );

        if (raw === null) {

            return;
        }

        const conflict = JSON.parse(raw);

        if (
            !conflict ||

            !payload ||

            conflict.request_id
                !== payload.request_id ||

            conflict.performance_session_id
                !== payload.performance_session_id ||

            conflict.question_id
                !== payload.question_id ||

            ![
                400, 401, 403, 404, 409, 422
            ].includes(conflict.http_status) ||

            typeof conflict.message !== "string"
        ) {

            throw new Error(
                "Saklanan cevap uyuşmazlığı " +
                "doğrulanamadı."
            );
        }

        this.responseConflict = Object.freeze({

            http_status:
                conflict.http_status,

            request_id:
                conflict.request_id,

            performance_session_id:
                conflict.performance_session_id,

            question_id:
                conflict.question_id,

            message:
                conflict.message
        });

        this.reconciliationRequired = true;
    }


    clearStoredResponseConflict() {

        sessionStorage.removeItem(
            this.responseConflictStorageKey
        );

        this.responseConflict = null;
    }


    get hasResponseConflict() {

        return this.responseConflict !== null;
    }


    classifyResponseFailure(error, payload) {

        if (!this.pendingResponse) {

            return;
        }

        const permanentStatuses = [

            400,

            401,

            403,

            404,

            409,

            422
        ];

        if (
            permanentStatuses.includes(
                error.httpStatus
            )
        ) {

            this.responseConflict = Object.freeze({

                http_status:
                    error.httpStatus,

                request_id:
                    payload.request_id,

                performance_session_id:
                    payload.performance_session_id,

                question_id:
                    payload.question_id,

                message:
                    error.message
            });

            try {

                this.persistResponseConflict();

            } catch (storageError) {

                this.reconciliationRequired = true;

                throw new Error(
                    "Cevap uyuşmazlığı güvenli biçimde " +
                    "saklanamadı. Öğretmeninize bildiriniz."
                );
            }
        }
    }


    async sendPendingResponse() {

        if (this.busy || !this.pendingResponse) {

            throw new Error(
                "Gönderilecek cevap bulunmuyor."
            );
        }

        this.busy = true;

        const payload = this.pendingResponse;

        try {

            if (this.hasResponseConflict) {

                throw new Error(
                    "Cevap kaydı öğretmen tarafından " +
                    "kontrol edilmelidir."
                );
            }


            if (
                this.hasStaleStoredResponse ||

                payload.performance_session_id
                    !== this.performanceSessionId
            ) {

                throw new Error(
                    "Bekleyen cevap farklı bir " +
                    "öğrenme oturumuna ait."
                );
            }


            const result = await this.apiRequest(

                this.endpoint + "/response",

                "POST",

                payload
            );

            this.validateResponseAcknowledgement(
                result,
                payload
            );

            // The response has been acknowledged.
            // Never submit this interaction as a new attempt.

            this.clearStoredPendingResponse();

            this.pendingResponse = null;

            // Retrieve authoritative execution state
            // before allowing another operation.

            this.reconciliationRequired = true;

            const latest = await this.apiRequest(
                this.endpoint
            );

            this.applyExecutionState(latest);

            this.reconciliationRequired = false;

            const decisionMatchesCurrentRound = (

                this.currentQuestion.question_id
                    === result.question_id &&

                this.currentQuestion.attempt_count
                    === result.attempt.attempt_number &&

                this.execution.status
                    === result.progression.execution_status
            );

            return {

                response: result,

                execution: this.execution,

                feedback_applicable:
                    decisionMatchesCurrentRound
            };

        } catch (error) {

            this.reconciliationRequired = true;

            this.classifyResponseFailure(
                error,
                payload
            );

            throw error;

        } finally {

            this.busy = false;
        }
    }


    async retryPendingResponse() {

        if (this.hasResponseConflict) {

            throw new Error(
                "Cevap kaydı öğretmen tarafından " +
                "kontrol edilmelidir."
            );
        }


        if (this.busy || !this.pendingResponse) {

            throw new Error(
                "Tekrar gönderilecek cevap bulunmuyor."
            );
        }

        // Reuse the original immutable payload,
        // including the original request ID.

        return this.sendPendingResponse();
    }


    get hasPendingResponse() {

        return this.pendingResponse !== null;
    }


    async loadExecution() {

        if (this.busy) {

            throw new Error(
                "Devam eden bir işlem bulunuyor."
            );
        }

        this.busy = true;

        try {

            const result = await this.apiRequest(
                this.endpoint
            );

            this.applyExecutionState(result);

            const recoveryStatus =
                this.restorePendingResponse();

            this.reconciliationRequired = (
                recoveryStatus !== "NO_PENDING_RESPONSE" ||

                this.hasResponseConflict
            );

            return this.execution;

        } catch (error) {

            this.reconciliationRequired = true;

            throw error;

        } finally {

            this.busy = false;
        }
    }
}

window.StudentExecutionController =
    StudentExecutionController;
