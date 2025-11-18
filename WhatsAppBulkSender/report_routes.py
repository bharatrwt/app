from flask import Blueprint, request, jsonify, Response, session
from auth import login_required, admin_required
from firebase_utils import (
    get_document, get_all_documents, query_documents,
    MESSAGES_COLLECTION, MESSAGE_RECIPIENTS_COLLECTION, TASKS_COLLECTION
)
import csv
from io import StringIO

report_bp = Blueprint('reports', __name__)


@report_bp.route('/api/task/<task_id>', methods=['GET'])
@login_required
def get_task_report(task_id):
    """Get aggregated report for a specific task"""
    task = get_document(TASKS_COLLECTION, task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Verify access (admin can see all, users can only see their tasks)
    if session.get('role') != 'admin' and task.get('assigned_user_id') != session.get('user_id'):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get all messages for this task
    messages = query_documents(MESSAGES_COLLECTION, 'task_id', '==', task_id)
    
    # Aggregate stats
    total_delivered = 0
    total_seen = 0
    total_replies = 0
    total_sent = 0
    total_failed = 0
    total_recipients = 0
    
    for message in messages:
        stats = message.get('stats', {})
        total_delivered += stats.get('delivered', 0)
        total_seen += stats.get('seen', 0)
        total_replies += stats.get('replied', 0)
        total_sent += stats.get('sent', 0)
        total_failed += stats.get('failed', 0)
        total_recipients += message.get('total_recipients', 0)
    
    return jsonify({
        'task': task,
        'total_messages': len(messages),
        'total_recipients': total_recipients,
        'total_sent': total_sent,
        'total_delivered': total_delivered,
        'total_seen': total_seen,
        'total_replies': total_replies,
        'total_failed': total_failed,
        'messages': messages
    })


@report_bp.route('/api/admin/reports', methods=['GET'])
@admin_required
def get_admin_reports():
    """Get reports with filtering (admin only)"""
    task_id = request.args.get('task_id')
    task_title = request.args.get('task_title')
    
    results = []
    
    if task_id:
        # Get report for specific task
        task = get_document(TASKS_COLLECTION, task_id)
        if task:
            messages = query_documents(MESSAGES_COLLECTION, 'task_id', '==', task_id)
            
            # Aggregate stats
            stats = aggregate_message_stats(messages)
            stats['task'] = task
            results.append(stats)
    
    elif task_title:
        # Search tasks by title
        all_tasks = get_all_documents(TASKS_COLLECTION)
        matching_tasks = [t for t in all_tasks if task_title.lower() in t.get('title', '').lower()]
        
        for task in matching_tasks:
            messages = query_documents(MESSAGES_COLLECTION, 'task_id', '==', task['id'])
            stats = aggregate_message_stats(messages)
            stats['task'] = task
            results.append(stats)
    
    else:
        # Get all tasks with reports
        all_tasks = get_all_documents(TASKS_COLLECTION)
        
        for task in all_tasks:
            messages = query_documents(MESSAGES_COLLECTION, 'task_id', '==', task['id'])
            if messages:  # Only include tasks that have messages
                stats = aggregate_message_stats(messages)
                stats['task'] = task
                results.append(stats)
    
    return jsonify({'reports': results})


@report_bp.route('/api/user/reports', methods=['GET'])
@login_required
def get_user_reports():
    """Get reports for user's assigned tasks"""
    # Get user's tasks
    tasks = query_documents(TASKS_COLLECTION, 'assigned_user_id', '==', session['user_id'])
    
    results = []
    for task in tasks:
        messages = query_documents(MESSAGES_COLLECTION, 'task_id', '==', task['id'])
        if messages:
            stats = aggregate_message_stats(messages)
            stats['task'] = task
            results.append(stats)
    
    return jsonify({'reports': results})


@report_bp.route('/api/reports/export', methods=['GET'])
@login_required
def export_report():
    """Export report to CSV"""
    task_id = request.args.get('task_id')
    
    if not task_id:
        return jsonify({'error': 'task_id is required'}), 400
    
    task = get_document(TASKS_COLLECTION, task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Verify access
    from flask import session
    if session.get('role') != 'admin' and task.get('assigned_user_id') != session.get('user_id'):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get all messages and recipients for this task
    messages = query_documents(MESSAGES_COLLECTION, 'task_id', '==', task_id)
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow([
        'Message ID',
        'Recipient Phone',
        'Status',
        'Sent At',
        'Delivered At',
        'Seen At',
        'Reply Text',
        'Reply At'
    ])
    
    # Write data
    for message in messages:
        recipients = query_documents(MESSAGE_RECIPIENTS_COLLECTION, 'message_id', '==', message['id'])
        
        for recipient in recipients:
            writer.writerow([
                message['id'],
                recipient.get('phone_number', ''),
                recipient.get('status', ''),
                message.get('created_at', ''),
                recipient.get('delivered_at', ''),
                recipient.get('seen_at', ''),
                recipient.get('reply_text', ''),
                recipient.get('reply_at', '')
            ])
    
    # Return CSV file
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=report_task_{task_id}.csv'}
    )


def aggregate_message_stats(messages):
    """Helper function to aggregate stats from multiple messages"""
    total_delivered = 0
    total_seen = 0
    total_replies = 0
    total_sent = 0
    total_failed = 0
    total_recipients = 0
    
    for message in messages:
        stats = message.get('stats', {})
        total_delivered += stats.get('delivered', 0)
        total_seen += stats.get('seen', 0)
        total_replies += stats.get('replied', 0)
        total_sent += stats.get('sent', 0)
        total_failed += stats.get('failed', 0)
        total_recipients += message.get('total_recipients', 0)
    
    return {
        'total_messages': len(messages),
        'total_recipients': total_recipients,
        'total_sent': total_sent,
        'total_delivered': total_delivered,
        'total_seen': total_seen,
        'total_replies': total_replies,
        'total_failed': total_failed
    }
