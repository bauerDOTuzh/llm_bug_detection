<?php foreach ($crumbs as $item) : ?>
  <tr id="attachment_<?= $item->id ?>" title="<?= $item->thema ?>">
    <td><?= $item->id ?></td>
    <td><?= $item->filename ?></td>
    <td><?= $item->record_lang ?></td>
    <td><?= Utils::formatBytes($item->filesize) ?></td>
    <td><?= $item->mime_type ?></td>
    <td>
      <button class="btn btn-danger btn-delete-attachment" title="<?= Translation::get('ad_gen_delete') ?>"
              data-attachment-id="<?= $item->id ?>"
              data-csrf="<?= Token::getInstance()->getTokenString('delete-attachment') ?>">
        <i aria-hidden="true" class="fa fa-trash btn-delete-attachment" data-attachment-id="<?= $item->id ?>"
              data-csrf="<?= Token::getInstance()->getTokenString('delete-attachment') ?>"></i>
      </button>
    </td>
    <td>
      <a title="<?= Translation::get('ad_entry_faq_record') ?>" class="btn btn-info"
          href="../index.php?action=faq&id=<?= $item->record_id ?>&lang=<?= $item->record_lang ?>">
        <i aria-hidden="true" class="fa fa-link"></i>
      </a>
    </td>
  </tr>
<?php endforeach; ?>