//! Counter acceptance against a disposable, fee-free localhost chain.
use anyhow::{ensure, Context, Result};
use integration::helpers::{
    counter_storage_slot, create_account_from_package, create_basic_wallet_account,
    wait_for_commit, AccountCreationConfig, COUNTER_STORAGE_KEY,
};
use miden_client::{
    account::{component::InitStorageData, StorageMapKey},
    builder::ClientBuilder,
    keystore::FilesystemKeyStore,
    rpc::Endpoint,
    transaction::TransactionRequestBuilder,
    utils::Deserializable,
};
use miden_client_sqlite_store::ClientBuilderSqliteExt;
use miden_mast_package::Package;
use miden_standards::testing::note::NoteBuilder;
use std::{path::PathBuf, sync::Arc, time::Duration};

#[tokio::main]
async fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    ensure!(args.len() == 5, "Usage: local-counter-validation <http://127.0.0.1:port> <new-state-dir> <project-contracts-dir> <expected-count>");
    let endpoint = Endpoint::try_from(args[1].as_str()).map_err(anyhow::Error::msg)?;
    ensure!(
        endpoint.protocol() == "http"
            && endpoint.host() == "127.0.0.1"
            && endpoint.port().is_some(),
        "Only explicit IPv4 loopback RPC is accepted"
    );
    let state = PathBuf::from(&args[2]);
    let contracts = PathBuf::from(&args[3]);
    let expected: u64 = args[4]
        .parse()
        .context("Expected count must be an integer")?;
    // Refuse existing state. Never wipe or reuse a wallet/store.
    std::fs::create_dir(&state).context("State directory must be new")?;
    tokio::time::timeout(
        Duration::from_secs(180),
        validate(endpoint, state, contracts, expected),
    )
    .await
    .context("Local counter validation exceeded 180 seconds")??;
    Ok(())
}

async fn validate(
    endpoint: Endpoint,
    state: PathBuf,
    contracts: PathBuf,
    expected: u64,
) -> Result<()> {
    let load = |name: &str| -> Result<Package> {
        let bytes = std::fs::read(contracts.join(name).join("target/miden/release/out.masp"))?;
        Package::read_from_bytes(&bytes).context("Rebuild packages with the pinned compiler")
    };
    let counter_package = Arc::new(load("counter-account")?);
    let note_package = load("increment-note")?;
    let keystore = Arc::new(FilesystemKeyStore::new(state.join("keystore"))?);
    let mut client = ClientBuilder::new()
        .grpc_client(&endpoint, Some(5_000))
        .sqlite_store(state.join("store.sqlite3"))
        .authenticator(keystore.clone())
        .build()
        .await?;
    let synced = client.sync_state().await?;
    println!("PASS sync at block {}", synced.block_num);
    let header = client.get_latest_block_header().await?;
    ensure!(
        header.fee_parameters().verification_base_fee() == 0,
        "Validator requires a fee-free disposable chain"
    );
    println!("PASS verification base fee: 0");

    let slot = counter_storage_slot()?;
    let mut storage = InitStorageData::default();
    storage.insert_map_entry(slot.clone(), COUNTER_STORAGE_KEY, 0_u64)?;
    let counter = create_account_from_package(
        &mut client,
        counter_package,
        AccountCreationConfig {
            init_storage_data: storage,
            ..Default::default()
        },
    )
    .await?;
    let sender = create_basic_wallet_account(&mut client, keystore, Default::default()).await?;
    println!("Counter account ID: {}", counter.id().to_hex());
    let note = NoteBuilder::new(sender.id(), client.rng())
        .package(note_package)
        .tag(0)
        .build()?;
    let publish = TransactionRequestBuilder::new()
        .own_output_notes(vec![note.clone()])
        .build()?;
    let publish_id = client.submit_new_transaction(sender.id(), publish).await?;
    wait_for_commit(&mut client, publish_id).await?;
    println!("PASS publish committed {}", publish_id.to_hex());
    let consume = TransactionRequestBuilder::new()
        .input_notes([(note, None)])
        .build()?;
    let consume_id = client.submit_new_transaction(counter.id(), consume).await?;
    wait_for_commit(&mut client, consume_id).await?;
    println!("PASS consume committed {}", consume_id.to_hex());
    let account = client
        .get_account(counter.id())
        .await?
        .context("Counter absent after commit")?;
    let actual = account
        .storage()
        .get_map_item(&slot, StorageMapKey::new(COUNTER_STORAGE_KEY))?[0]
        .as_canonical_u64();
    ensure!(
        actual == expected,
        "Counter assertion failed: expected {expected}, got {actual}"
    );
    println!("PASS committed counter value: {actual}");
    Ok(())
}
